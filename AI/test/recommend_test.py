import re
import os
import pdfplumber
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import time


# 환경 변수 설정
os.environ["TOKENIZERS_PARALLELISM"] = "false"

pdf_dirs = {
    "실손보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../상품요약서/실손보험')),
    "건강보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../상품요약서/건강보험(암 등)')),
    "종신보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../상품요약서/종신보험')),
    "정기보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../상품요약서/정기보험')),
    "기타": os.path.abspath(os.path.join(os.path.dirname(__file__), '../상품요약서/기타')),
}

# 추천 결과를 저장할 리스트
recommendation_results = []

model = SentenceTransformer("jhgan/ko-sroberta-multitask")
# pdf_dir = "/Users/ddinga/Downloads/요약서실손보험"

# PDF에서 텍스트 추출 함수
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

# 사용자 입력 정의
# user_input = {
#     "성별": "남성",
#     "나이": "43",
#     "흡연여부": "예",
#     "음주빈도": "없음",
#     "운동빈도": "없음",
#     "부양가족여부": "있음",
#     "연소득(만원)": 6000,
#     "가입목적": "실손보험",
#     "선호보장기간": 10,
#     "보험료납입주기": "분기납",
# }

# 나이 등급화 함수
def get_age_group(age):
    age = int(age)
    if age < 30:
        return '20대 이하'
    elif age < 40:
        return '30대'
    elif age < 50:
        return '40대'
    elif age < 60:
        return '50대'
    else:
        return '60대 이상'
    
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
                continue  # 카테고리는 포함하지 않음
            
            elif key == '선호보장기간':
                result['선호보장기간'] = 10
            
            else:
                result[key] = value
    return result

# 숫자 필드와 텍스트 필드 구분
numeric_fields = ["연소득(만원)", "선호보장기간"]
text_fields = ["성별", "나이", "흡연여부", "음주빈도", "운동빈도", "부양가족여부", "가입목적", "보험료납입주기"]

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
    for field, user_value in user_input.items():
        if field in numeric_fields:
            user_value = float(user_value)
            matches = re.findall(r"(\d+\.?\d*)", product_text)
            if matches:
                product_values = [float(value) for value in matches]
                closest_value = min(product_values, key=lambda x: abs(x - user_value))
                if abs(user_value - closest_value) / user_value < 0.1:  # 10% 이내 차이로 유사하면 이유 추가
                    reasons.append(f"{field}이(가) 유사합니다.")
        elif field in text_fields:
            if str(user_value) in product_text:
                reasons.append(f"{field}이(가) 일치합니다.")
    return reasons

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
        reasons = generate_reasons(user_input, product_text)
        results.append({
            "상품명": filename,
            "총점": total_score,
            "추천 이유": ", ".join(reasons),
        })

    results = sorted(results, key=lambda x: x["총점"], reverse=True)
    return results[:k]

# 추천 실행

with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '../random_data.json')), 'r', encoding='utf-8') as f:
    user_inputs = json.load(f)

recommendation_results = []

for user_input in user_inputs:
    
    category = user_input["가입목적및개인선호"].get("카테고리")  # 카테고리 추출
    pdf_dir = pdf_dirs.get(category)
    user_query = json_to_query(user_input)
    print(user_query)
    
    top_3_recommendations = recommend_top_k_products(user_query, pdf_dir, model, k=3)

    
    output_data = {
        "user_query": user_query,
    }
    
    recommendation_results.append(output_data)
    
    # 결과 출력
    for idx, rec in enumerate(top_3_recommendations):
        print(f"Top {idx+1}: {rec['상품명']}, 총점: {rec['총점']:.2f}")
        print(f"추천 이유: {rec['추천 이유']}")
        print("------")

        recommendation = {
            'product_name': rec['상품명'],
            'similarity_score': rec['총점'],
            # 'reason': rec['추천 이유']
        }
        

        recommendation_results.append(recommendation)
        
    with open('recommendations_result.json', 'w', encoding='utf-8') as f:
        json.dump(recommendation_results, f, ensure_ascii=False, indent=4)