from django.apps import AppConfig
from keybert import KeyBERT

from sentence_transformers import SentenceTransformer
import faiss
import os
import pdfplumber
import numpy as np
import re


os.environ["TOKENIZERS_PARALLELISM"] = "false"

pdf_dirs = {
    "실손보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/실손보험')),
    "건강보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/건강보험(암 등)')),
    "종신보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/종신보험')),
    "정기보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/정기보험')),
    "기타": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/기타')),
}

model = None

# 데이터 저장을 위한 전역 변수
rag_models = {}

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

def initialize_rag_model(pdf_dir):
    global model 
    
    # PDF에서 텍스트와 파일 이름 추출
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
    
    return {
        # "texts": texts,
        # "filenames": filenames,
        "texts_and_filenames" : texts_and_filenames,
        "embeddings": embeddings,
        "index": index,
        # "model": model,
        "kw_model": kw_model
    }

class SuggestionConfig(AppConfig):
    name = 'suggestion'

    def ready(self):
        global rag_models
        
        # 각 보험 종류에 대해 RAG 모델 초기화
        for insurance_type, dir_path in pdf_dirs.items():
            if os.path.exists(dir_path):  # 폴더가 존재하는 경우에만 초기화
                rag_models[insurance_type] = initialize_rag_model(dir_path)
            else:
                print(f"폴더가 존재하지 않습니다: {dir_path}")
        
