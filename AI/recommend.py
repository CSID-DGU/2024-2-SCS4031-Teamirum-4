import json
import os
import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import re
#from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
#import torch
from sklearn.metrics.pairwise import cosine_similarity
from keybert import KeyBERT

# 환경 변수 설정
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 추천 결과를 저장할 리스트
recommendation_results = []

# 텍스트 추출 및 파일 이름과 연결
def extract_texts_and_filenames(pdf_dir):
    texts_and_filenames = []
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            with pdfplumber.open(os.path.join(pdf_dir, filename)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + " "
                cleaned_text = clean_text(text)
                texts_and_filenames.append((cleaned_text, filename))  # 텍스트와 파일 이름 저장
    return texts_and_filenames

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # 불필요한 공백 제거
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣.,!?]', '', text)  # 특수문자 제거
    return text.strip()

# 한국어 불용어 리스트
korean_stopwords = ['그', '그리고', '그러나', '하지만', '또한', '등', '등의', '이', '있습니다', '수', '있는', '하는', '할', '합니다', '따라']

# 사용자 입력 파싱 함수
def parse_user_input(user_input):
    user_data = {}
    for item in user_input.split(','):
        key_value = item.split(':')
        if len(key_value) == 2:
            key, value = key_value
            user_data[key.strip()] = value.strip()
    return user_data


# 추천 이유 생성
def generate_reason_with_keywords(user_query, recommended_text, similarity_score, kw_model, top_n=3):
    # 사용자 입력에서 키워드 추출
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

# PDF에서 텍스트와 파일 이름 추출
pdf_dir = "C:/Users/kehah/Desktop/상품요약서"
texts_and_filenames = extract_texts_and_filenames(pdf_dir)
texts = [item[0] for item in texts_and_filenames]
filenames = [item[1] for item in texts_and_filenames]

# 텍스트 임베딩 생성
model = SentenceTransformer('jhgan/ko-sroberta-multitask')
embeddings = model.encode(texts, normalize_embeddings=True)

# KeyBERT 모델 생성
kw_model = KeyBERT(model)

# FAISS 인덱스 설정
embedding_dim = embeddings.shape[1]
index = faiss.IndexFlatIP(embedding_dim)
index.add(np.array(embeddings))

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

# 사용자 입력 파싱 및 쿼리 생성
user_input = "이름: 홍길동, 성별: 여성, 나이: 54, 신장(cm): 165, 체중(kg): 50, 흡연여부: 예, 음주빈도: 자주, 운동빈도: 가끔, 부양가족여부: 없음, 연소득(만원): 3000, 가입목적: 질병, 선호보장기간: 20년, 보험료납입주기: 월납"
user_data = parse_user_input(user_input)

# 나이 등급화 적용
if '나이' in user_data:
    user_data['나이'] = get_age_group(user_data['나이'])

important_fields = ['성별', '나이', '흡연여부', '음주빈도', '운동빈도', '부양가족여부', '연소득(만원)', '가입목적', '선호보장기간', '보험료납입주기']
user_query = ', '.join([f"{field}: {user_data.get(field, '')}" for field in important_fields])
    
# 사용자 임베딩 생성
user_embedding = model.encode([user_query], normalize_embeddings=True)

# 유사도 검색
k = 3
distances, indices = index.search(user_embedding.astype(np.float32), k)
recommendations = [texts_and_filenames[i] for i in indices[0]]

# RAG 기반 추천
print("RAG 기반 추천 결과:")
for i, (rec_text, rec_filename) in enumerate(recommendations):
    product_name = rec_filename  # 파일 이름을 상품명으로 사용
    similarity_score = float(distances[0][i])
    reason = generate_reason_with_keywords(user_query, rec_text, similarity_score, kw_model)

    # 추천 결과를 딕셔너리로 저장
    recommendation = {
        'product_name': product_name,
        'summary_text': rec_text,
        'similarity_score': similarity_score,
        'reason': reason
    }
    recommendation_results.append(recommendation)

    # 출력
    print(f"Top {i+1}: {product_name}")
    #print(f"요약: {summary_text}")
    print(f"추천 이유: {reason}")
    print("------")

# 추천 결과를 JSON 파일로 저장
with open('recommendations.json', 'w', encoding='utf-8') as f:
    json.dump(recommendation_results, f, ensure_ascii=False, indent=4)