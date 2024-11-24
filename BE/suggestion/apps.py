from django.apps import AppConfig
from sentence_transformers import SentenceTransformer
import faiss
import os
import pdfplumber
import numpy as np
from transformers import pipeline

pdf_dir = pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../삼성생명'))
model_path = 'all-MiniLM-L6-v2'
summarization_model_name = "snunlp/KR-Summarization"

texts = []
embeddings = None
index = None
model = None
generator = None

# 텍스트 전처리 함수
def clean_text(text):
    import re
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣.,!?]', '', text)
    return text.strip()

# PDF에서 텍스트 추출
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

def initialize_rag_model():
    global texts, embeddings, index, model, generator
    
    # PDF 텍스트 추출
    texts = extract_text_from_pdfs(pdf_dir)

    # 임베딩 및 인덱스 생성
    model = SentenceTransformer(model_path)
    embeddings = model.encode(texts, normalize_embeddings=True)
    embedding_dim = embeddings.shape[1]
    
    index = faiss.IndexFlatIP(embedding_dim)
    index.add(np.array(embeddings))
    
    # 요약 모델 초기화
    try:
        generator = pipeline("summarization", model=summarization_model_name, tokenizer=summarization_model_name)
    except Exception as e:
        print(f"요약 모델 로드 중 오류 발생: {e}")
        generator = None

class SuggestionConfig(AppConfig):
    name = 'suggestion'

    def ready(self):
        initialize_rag_model()
        
