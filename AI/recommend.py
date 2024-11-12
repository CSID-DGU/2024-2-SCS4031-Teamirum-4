import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
from transformers import pipeline, AutoTokenizer
import re

# 텍스트 추출 및 전처리
def extract_text_from_pdfs(pdf_dir):
    texts = []
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            with pdfplumber.open(os.path.join(pdf_dir, filename)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + " "
                cleaned_text = clean_text(text)
                texts.append(cleaned_text)
    return texts

def clean_text(text):
    # 불필요한 공백 제거
    text = re.sub(r'\s+', ' ', text)
    # 한국어의 경우 일부 특수 문자는 유용할 수 있으므로 제거 범위를 조정
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣.,!?]', '', text)
    return text.strip()

# PDF에서 텍스트 추출
pdf_dir = "/Users/ddinga/Downloads/삼성생명_보험약관" 
texts = extract_text_from_pdfs(pdf_dir)

# 텍스트 임베딩 생성
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts, normalize_embeddings=True)

# FAISS 인덱스 (코사인 유사도: Inner Product 사용)
embedding_dim = embeddings.shape[1]
index = faiss.IndexFlatIP(embedding_dim)
index.add(np.array(embeddings))

# 사용자 입력 벡터화
user_query = "50대, 질병 보장, 월 10만원"  # 사용자 입력 예시
user_embedding = model.encode([user_query], normalize_embeddings=True)

# 유사도 기반 검색
k = 5  # 상위 5개 추천
distances, indices = index.search(np.array(user_embedding), k)
recommendations = [texts[i] for i in indices[0]]

# 한국어 생성 모델
summarization_model_name = "snunlp/KR-Summarization"
try:
    generator = pipeline("summarization", model=summarization_model_name, tokenizer=summarization_model_name)
except Exception as e:
    print(f"요약 모델 로드 중 오류 발생: {e}")
    generator = None

# 텍스트 분할
def split_text(text, max_length=512):
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        # 현재 청크에 추가할 시퀀스 길이를 계산
        if len(current_chunk) + len(sentence) + 1 < max_length:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# RAG 기반 추천 결과
print("RAG 기반 추천 결과:")
for i, rec in enumerate(recommendations):
    if generator:
        try:
            # 텍스트를 토큰 단위로 제한하여 분할
            chunks = split_text(rec, max_length=512)
            generated_summaries = []
            for chunk in chunks:
                summary = generator(chunk, max_length=100, min_length=30, do_sample=False)
                generated_summaries.append(summary[0]['summary_text'])
            summary_text = " ".join(generated_summaries)
        except Exception as e:
            print(f"요약 생성 중 오류 발생: {e}")
            summary_text = rec[:500] + "..."  # 요약 실패 시 일부 텍스트 표시
    else:
        summary_text = rec[:500] + "..."  # 요약 모델 로드 실패 시 일부 텍스트 표시

    print(f"추천 {i+1}:")
    print(summary_text)
    print("------")
