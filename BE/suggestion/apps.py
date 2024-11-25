from django.apps import AppConfig
from sentence_transformers import SentenceTransformer
import faiss
import os
import pdfplumber
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from keybert import KeyBERT
import re


os.environ["TOKENIZERS_PARALLELISM"] = "false"

pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서'))
summarization_model_name = "snunlp/KR-Summarization"

texts = []
texts_and_filenames = []
embeddings = None
index = None
model = None
kw_model = None

generator = None

# 텍스트 전처리 함수
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣.,!?]', '', text)
    return text.strip()

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

def initialize_rag_model():
    global texts, texts_and_filenames, embeddings, index, model, generator, kw_model
    
    # PDF에서 텍스트와 파일 이름 추출
    texts_and_filenames = extract_texts_and_filenames(pdf_dir)
    texts = [item[0] for item in texts_and_filenames]
    filenames = [item[1] for item in texts_and_filenames]

    # 텍스트 임베딩 생성
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts, normalize_embeddings=True)
    kw_model = KeyBERT(model)
    
    # FAISS 인덱스 설정
    embedding_dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(embedding_dim)
    index.add(np.array(embeddings))
    
    # 한국어 생성 모델 설정
    # try:
    #     tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
    #     summarization_model = AutoModelForCausalLM.from_pretrained(
    #         "facebook/bart-large-cnn",
    #         torch_dtype=torch.float16  # 메모리 최적화
    #     )
    #     generator = pipeline("text-generation", model=summarization_model, tokenizer=tokenizer, device=-1)
    # except Exception as e:
    #     print(f"요약 모델 로드 중 오류 발생: {e}")
    #     generator = None

class SuggestionConfig(AppConfig):
    name = 'suggestion'

    def ready(self):
        initialize_rag_model()
        
