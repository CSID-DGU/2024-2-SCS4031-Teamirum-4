from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
# from suggestion.apps import rag_models, model

import pdfplumber
import numpy as np
import json
import time
import os
import re

os.environ["TOKENIZERS_PARALLELISM"] = "false"

recommendation_results = []

model = SentenceTransformer("jhgan/ko-sroberta-multitask")


pdf_dirs = {
    "실손보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/실손보험')),
    "건강보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/건강보험(암 등)')),
    "종신보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/종신보험')),
    "정기보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/정기보험')),
    "기타": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/기타')),
}

numeric_fields = ["연소득(만원)", "선호보장기간"]
text_fields = ["성별", "나이", "흡연여부", "음주빈도", "운동빈도", "부양가족여부", "가입목적", "보험료납입주기"]

def extract_texts_and_filename(pdf_dir):
    texts_and_filenames = []
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(pdf_dir, filename)
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + " "
            texts_and_filenames.append((filename, text.strip()))
    return texts_and_filenames

# 숫자 필드 유사도 계산 함수
def calculate_numeric_similarity(user_input, product_text):
    similarities = []
    for field in numeric_fields:
        user_value = user_input.get(field)
        if user_value is not None:
            user_value = float(user_value)
            matches = re.findall(r"(\d+\.?\d*)", product_text)  # 텍스트에서 모든 숫자 추출
            if matches:
                product_values = [float(value) for value in matches]
                closest_value = min(product_values, key=lambda x: abs(x - user_value))
                similarity = max(0, 1 - abs(user_value - closest_value) / user_value)
                similarities.append(similarity)
    if similarities:
        return np.mean(similarities)  # 평균 유사도 반환
    return 0

# 텍스트 필드 유사도 계산 함수
def calculate_text_similarity(user_input, product_text, model):
    user_text = " ".join([str(user_input.get(field, "")) for field in text_fields])
    product_text_embedded = model.encode([product_text], normalize_embeddings=True)
    user_text_embedded = model.encode([user_text], normalize_embeddings=True)
    similarity = cosine_similarity(user_text_embedded, product_text_embedded)[0][0]
    return similarity


# 추천 이유 생성 함수
def generate_reasons(user_input, product_text):
    reasons = []
    keywords = [] # 키워드 추출
    for field, user_value in user_input.items():
        if field in numeric_fields:
            user_value = float(user_value)
            matches = re.findall(r"(\d+\.?\d*)", product_text)
            if matches:
                product_values = [float(value) for value in matches]
                closest_value = min(product_values, key=lambda x: abs(x - user_value))
                if abs(user_value - closest_value) / user_value < 0.1:  # 10% 이내 차이로 유사하면 이유 추가
                    reasons.append(f"{field}이(가) 유사합니다.")
                    keywords.append(f"#{field}") # 키워드 추출
        elif field in text_fields:
            if str(user_value) in product_text:
                reasons.append(f"{field}이(가) 일치합니다.")
                keywords.append(f"#{field}") # 키워드 추출 
    return reasons, keywords

# 텍스트 분할 함수
def split_text(text, max_length=512):
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 < max_length:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def json_to_query(data):
    result = {}
    for category, details in data.items():
        for key, value in details.items():
            if key == '생년월일':
                birth_year, birth_month, birth_day = map(int, value.split('-'))
                age = time.localtime().tm_year - birth_year
                if age < 20:
                    age_group = '10대'
                elif age < 30:
                    age_group = '20대'
                elif age < 40:
                    age_group = '30대'
                elif age < 50:
                    age_group = '40대'
                elif age < 60:
                    age_group = '50대'
                else:
                    age_group = '60대 이상'
                result["나이"] = age_group
            
            elif key == '카테고리':
                result['가입목적'] = value
            
            # elif key == '선호보장기간':
            #     result['선호보장기간'] = 10
            
            else:
                result[key] = value
    return result


# 추천 이유 생성
def generate_reason_with_keywords(user_query, recommended_text, similarity_score, kw_model, top_n=3):
    # 사용자 입력에서 키워드 추출
    korean_stopwords = ['그', '그리고', '그러나', '하지만', '또한', '등', '등의', '이', '있습니다', '수', '있는', '하는', '할', '합니다', '따라']

    user_keywords = [kw for kw, score in kw_model.extract_keywords(user_query, keyphrase_ngram_range=(1,2), stop_words=korean_stopwords, top_n=10)]
    
    # 추천 텍스트에서 키워드 추출
    text_keywords = [kw for kw, score in kw_model.extract_keywords(recommended_text, keyphrase_ngram_range=(1,2), stop_words=korean_stopwords, top_n=30)]
    
    # 키워드 임베딩 생성
    user_kw_embeddings = model.encode(user_keywords, normalize_embeddings=True)
    text_kw_embeddings = model.encode(text_keywords, normalize_embeddings=True)
    
    # 유사도 계산
    similarity_matrix = cosine_similarity(user_kw_embeddings, text_kw_embeddings)
    max_sim_indices = similarity_matrix.argmax(axis=1)
    max_sim_values = similarity_matrix.max(axis=1)
    
    # 유사한 키워드 추출
    similar_keywords = set()
    for idx, sim_value in enumerate(max_sim_values):
        if sim_value > 0.7:  # 유사도 임계값 조정 가능
            similar_keywords.add(text_keywords[max_sim_indices[idx]])
    
    # 추천 이유 생성
    if similar_keywords:
        reason = f"사용자 입력과 주요 내용은 ('{', '.join(similar_keywords)}')(이)가 연관이 있습니다. "
    else:
        reason = "사용자 입력과 연관된 키워드는 없지만 문맥적으로 유사도가 높습니다. "
    
    reason += f"사용자와의 유사도 점수는 {similarity_score:.2f}입니다."
    return reason
    
# 보험상품별 점수 계산 및 추천
def recommend_top_k_products(user_input, pdf_dir, model, k=3):
    texts_and_filenames = extract_texts_and_filename(pdf_dir)
    results = []
    scaler = MinMaxScaler()  # 정규화용 스케일러

    # 유사도 계산
    numeric_similarities = []
    text_similarities = []
    for filename, product_text in texts_and_filenames:
        numeric_similarity = calculate_numeric_similarity(user_input, product_text)
        text_similarity = calculate_text_similarity(user_input, product_text, model)
        numeric_similarities.append(numeric_similarity)
        text_similarities.append(text_similarity)

    # 정규화
    numeric_similarities = scaler.fit_transform(np.array(numeric_similarities).reshape(-1, 1)).flatten()
    text_similarities = scaler.fit_transform(np.array(text_similarities).reshape(-1, 1)).flatten()

    # 총점 계산 및 추천 이유 생성
    for idx, (filename, product_text) in enumerate(texts_and_filenames):
        total_score = 0.5 * numeric_similarities[idx] + 0.5 * text_similarities[idx]
        # reasons = generate_reasons(user_input, product_text)
        reasons, keywords = generate_reasons(user_input, product_text) # 키워드 추출
        results.append({
            "상품명": filename,
            "총점": total_score,
            "추천 이유": ", ".join(reasons),
            "추천 키워드": keywords, # 키워드 추출
        })

    results = sorted(results, key=lambda x: x["총점"], reverse=True)
    return results[:k]
    
class SuggestionAPIView(APIView):
    # post로 바꿔야됨
    def post(self, request):
        try:
            # 프론트엔드에서 데이터 받기
            user_input = request.data
            
            category = user_input["가입목적및개인선호"].get("카테고리")  # 카테고리 추출
            pdf_dir = pdf_dirs.get(category)
            
            print(pdf_dir)
            
            user_query = json_to_query(user_input)
            print(user_query)
            
            top_3_recommendations = recommend_top_k_products(user_query, pdf_dir, model, k=3)

            recommendation_results = []

            recommendation_category = []
            recommendation_category.append(category)

            for idx, rec in enumerate(top_3_recommendations):
                print(f"Top {idx+1}: {rec['상품명']}, 총점: {rec['총점']:.2f}")
                print(f"추천 이유: {rec['추천 이유']}")
                print("------")

                recommendation = {
                    'product_name': rec['상품명'],
                    'similarity_score': rec['총점'],
                    'reason': rec['추천 이유'],
                    'keywords': rec['추천 키워드'] # 키워드 추출
                }
                
                recommendation_results.append(recommendation)
                
                
            # 현재 디렉토리 확인
            current_dir = os.getcwd()
            
            # 상위 디렉토리 경로 계산
            parent_dir = os.path.dirname(current_dir)
            
            # 상위 디렉토리에 파일 저장
            file_path = os.path.join(parent_dir, 'recommendations.json')
            # JSON 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(recommendation_results, f, ensure_ascii=False, indent=4)

            file_path = os.path.join(parent_dir, 'recommendations_category.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(recommendation_category, f, ensure_ascii=False, indent=4)
            # JSON 응답 생성
            return Response({"status": "success", "recommendations": recommendation_results})

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)
