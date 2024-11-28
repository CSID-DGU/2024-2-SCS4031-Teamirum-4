import openai
from openai import OpenAI
import streamlit as st
import json
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit.components.v1 as components
#OCR
import pdfplumber
from PIL import Image
import pytesseract

# OpenAI API 키 설정
client = OpenAI(api_key="")
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"


# 추천 결과를 JSON 파일에서 불러오기
with open('C:/Users/kehah/Desktop/2024-2-SCS4031-Teamirum-4/AI/recommendations.json', 'r', encoding='utf-8') as f:
    recommendation_results = json.load(f)
 

# JSON 파일 참조///
# recommendation_results = st.session_state.recommendation_results

# 텍스트 전처리 함수
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # 불필요한 공백 제거
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣.,!?]', '', text)  # 특수문자 제거
    return text.strip()


# GPT 응답 생성 함수
def ask_gpt(user_input, recommendation_results):
    terms_dir = "C:/Users/kehah/Desktop/상품요약서"  
    
    # 추천된 상품의 관련 내용을 수집
    context = "아래는 추천된 보험 상품 목록과 관련 내용입니다:\n"
    
    for idx, rec in enumerate(recommendation_results):
        product_name = rec.get('product_name', '상품명 없음')
        terms_filename = product_name  # 파일 이름과 약관 파일명이 일치시켜야함
        
        terms_path = os.path.join(terms_dir, terms_filename)
        relevant_text = ""
        
        if os.path.exists(terms_path):
            full_text = ""
            try:
                # 약관 파일 로드
                if terms_path.endswith('.pdf'):
                    with pdfplumber.open(terms_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                full_text += page_text + " "
                elif terms_path.endswith('.txt'):
                    with open(terms_path, 'r', encoding='utf-8') as f:
                        full_text = f.read()
                else:
                    print(f"지원하지 않는 파일 형식입니다: {terms_filename}")
                    full_text = ""
                
                # 텍스트 전처리
                full_text = clean_text(full_text)
                sentences = re.split(r'(?<=[.!?])\s+', full_text)
                
                # 문장 수 제한
                sentences = sentences[:1000]
                
                # 사용자 질문과 가장 유사한 문장 찾기
                vectorizer = TfidfVectorizer().fit(sentences)
                sentence_embeddings = vectorizer.transform(sentences)
                user_embedding = vectorizer.transform([user_input])
                
                similarities = cosine_similarity(user_embedding, sentence_embeddings)
                most_similar_idx = similarities.argsort()[0][-1]
                most_similar_sentence = sentences[most_similar_idx]
                
                relevant_text = most_similar_sentence
            except Exception as e:
                print(f"{terms_filename} 처리 중 오류 발생: {e}")
                relevant_text = "해당 상품의 약관을 처리하는 중 오류가 발생했습니다."
        else:
            relevant_text = "해당 상품의 약관을 찾을 수 없습니다."
        
        rec['relevant_text'] = relevant_text
        context += f"{idx+1}. {product_name}: {relevant_text}\n"

    messages = [
        {"role": "system", "content": "당신은 보험 상품에 대한 전문가로서 사용자에게 정보를 제공합니다."},
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": context},
        {"role": "user", "content": "위의 정보를 바탕으로 사용자의 질문에 가장 관련 있는 답변을 제공하세요."}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
            n=1,
            stop=None,
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        return f"Error: {str(e)}"

# OCR 처리 함수
def ocr_image_to_text(image):
    try:
        text = pytesseract.image_to_string(image, lang='kor')
        return clean_text(text)
    except Exception as e:
        return f"Error during OCR processing: {str(e)}"


# UI ( logo 추가 가능 )
st.title("티미룸 보험 챗봇입니다")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 파일 업로드 UI
uploaded_file = st.file_uploader("이미지 파일을 업로드하세요 (PNG, JPG)", type=["png", "jpg", "jpeg"])
# 사용자 입력
user_input = st.chat_input("질문을 입력하세요:")

# OCR 처리
ocr_text = ""
if uploaded_file:
    image = Image.open(uploaded_file)
    with st.spinner("이미지에서 텍스트를 추출 중..."):
        ocr_text = ocr_image_to_text(image)
    st.success("이미지에서 텍스트 추출이 완료되었습니다.")  


if user_input or ocr_text:

    combined_input = f"{user_input.strip()} {ocr_text.strip()}".strip()
    
    if not combined_input:  # 빈 값이면 처리 중단
        st.error("입력된 텍스트가 없습니다. 이미지를 업로드하거나 텍스트를 입력하세요.")
    else:
        # GPT에 질문
        assistant_response = ask_gpt(combined_input, recommendation_results)
    
        # 대화 상태 업데이트
        st.session_state.messages.append({"role": "user", "content": combined_input})
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    
        # 출력
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            st.markdown(assistant_response)