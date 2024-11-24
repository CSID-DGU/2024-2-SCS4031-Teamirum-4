import json
import os
import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import re
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from sklearn.metrics.pairwise import cosine_similarity

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

# 추천 이유 생성
def generate_reason_with_keywords(user_query, recommended_text, similarity_score, model, top_n=3):
    # 사용자 입력과 추천 텍스트를 단어 단위로 분리
    user_words = user_query.split()
    text_words = recommended_text.split()
    
    # 단어별 임베딩 생성
    user_embeddings = model.encode(user_words, normalize_embeddings=True)
    text_embeddings = model.encode(text_words, normalize_embeddings=True)
    
    # 유사도 계산
    similarities = cosine_similarity(user_embeddings, text_embeddings)
    
    # 유사도가 높은 단어 추출
    top_indices = similarities.max(axis=0).argsort()[-top_n:][::-1]
    keywords = [text_words[i] for i in top_indices if similarities[:, i].max() > 0.5]  # 유사도가 0.5 이상인 단어
    
    # 추천 이유 생성
    if keywords:
        reason = f"사용자 입력과 주요 키워드 ('{', '.join(keywords)}')가 연관이 있습니다. "
    else:
        reason = "사용자 입력과 연관된 명확한 키워드는 없지만 문맥적으로 유사도가 높습니다. "
    
    reason += f"텍스트와의 유사도 점수는 {similarity_score:.2f}입니다."
    return reason


# PDF에서 텍스트와 파일 이름 추출
pdf_dir = "/Users/ddinga/Downloads/상품요약서"
texts_and_filenames = extract_texts_and_filenames(pdf_dir)
texts = [item[0] for item in texts_and_filenames]
filenames = [item[1] for item in texts_and_filenames]

# 텍스트 임베딩 생성
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts, normalize_embeddings=True)

# FAISS 인덱스 설정
embedding_dim = embeddings.shape[1]
index = faiss.IndexFlatIP(embedding_dim)
index.add(np.array(embeddings))

# 사용자 입력
user_query = "50대, 질병보장, 월10만원"
user_embedding = model.encode([user_query], normalize_embeddings=True)

# 유사도 검색
k = 3
distances, indices = index.search(user_embedding.astype(np.float32), k)
recommendations = [texts_and_filenames[i] for i in indices[0]]

# 한국어 생성 모델 설정
try:
    tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
    summarization_model = AutoModelForCausalLM.from_pretrained(
        "facebook/bart-large-cnn",
        torch_dtype=torch.float16  # 메모리 최적화
    )
    generator = pipeline("text-generation", model=summarization_model, tokenizer=tokenizer, device=-1)
except Exception as e:
    print(f"요약 모델 로드 중 오류 발생: {e}")
    generator = None

# RAG 기반 추천
print("RAG 기반 추천 결과:")
for i, (rec_text, rec_filename) in enumerate(recommendations):
    product_name = rec_filename  # 파일 이름을 상품명으로 사용
    similarity_score = float(distances[0][i])
    reason = generate_reason_with_keywords(user_query, rec_text, similarity_score, model)

    # 추천 결과를 딕셔너리로 저장
    recommendation = {
        'product_name': product_name,
        'rec_text': rec_text,
        # 'summary_text': summary_text,
        'similarity_score': similarity_score,
        'reason': reason
    }
    recommendation_results.append(recommendation)

    # 출력
    print(f"추천 {i+1}: {product_name}")
    #print(f"요약: {summary_text}")
    print(f"추천 이유: {reason}")
    print("------")

# 추천 결과를 JSON 파일로 저장
with open('recommendations.json', 'w', encoding='utf-8') as f:
    json.dump(recommendation_results, f, ensure_ascii=False, indent=4)