import re
import os
import pdfplumber
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sentence_transformers import SentenceTransformer
import numpy as np
import json

# 환경 변수 설정
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 추천 결과를 저장할 리스트
recommendation_results = []

model = SentenceTransformer("jhgan/ko-sroberta-multitask")
pdf_dir = "/Users/ddinga/Downloads/요약서실손보험"

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
user_input = {
    "성별": "남성",
    "나이": "43",
    "흡연여부": "예",
    "음주빈도": "없음",
    "운동빈도": "없음",
    "부양가족여부": "있음",
    "연소득(만원)": 6000,
    "가입목적": "실손보험",
    "선호보장기간": 10,
    "보험료납입주기": "분기납",
}

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
    
# 나이를 계급화
if "나이" in user_input:
    user_input["나이"] = get_age_group(user_input["나이"])

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
        reasons, keywords = generate_reasons(user_input, product_text) # 키워드 추출
        results.append({
            "상품명": filename,
            "총점": total_score,
            "추천 이유": ", ".join(reasons),
            "추천 키워드": keywords, # 키워드 추출
        })

    results = sorted(results, key=lambda x: x["총점"], reverse=True)
    return results[:k]

# 추천 실행
top_3_recommendations = recommend_top_k_products(user_input, pdf_dir, model, k=3)

# 결과 출력
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

# 추천 결과를 JSON 파일로 저장
with open('recommendations.json', 'w', encoding='utf-8') as f:
    json.dump(recommendation_results, f, ensure_ascii=False, indent=4)