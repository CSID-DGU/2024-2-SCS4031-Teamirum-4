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

# 추천 결과를 JSON 파일에서 불러오기 및 세션 초기화

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
def ask_gpt(prompt, context):
    messages = [
        {"role": "system", "content": "당신은 보험 상품에 대한 전문가로서 사용자에게 정보를 제공합니다."},
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": context},
        {"role": "user", "content": "위의 정보를 바탕으로 질문에 답변해주세요."}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# 약관 내용 검색 함수
def search_terms(user_input, recommendation_results):
    terms_dir = "C:/Users/kehah/Desktop/상품요약서" 
    context = "추천된 보험 상품의 관련 약관 내용:\n"
    
    for idx, rec in enumerate(recommendation_results):
        product_name = rec.get('product_name', '상품명 없음')
        terms_filename = f"{product_name}.pdf"  # PDF 파일명
        
        terms_path = os.path.join(terms_dir, terms_filename)
        relevant_text = "관련 정보를 찾을 수 없습니다."
        
        if os.path.exists(terms_path):
            try:
                full_text = ""
                with pdfplumber.open(terms_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + " "
                full_text = clean_text(full_text)
                sentences = re.split(r'(?<=[.!?])\s+', full_text)
                
                vectorizer = TfidfVectorizer().fit(sentences)
                sentence_embeddings = vectorizer.transform(sentences)
                user_embedding = vectorizer.transform([user_input])
                
                similarities = cosine_similarity(user_embedding, sentence_embeddings)
                most_similar_idx = similarities.argsort()[0][-1]
                most_similar_sentence = sentences[most_similar_idx]
                
                relevant_text = most_similar_sentence
            except Exception as e:
                relevant_text = f"오류 발생: {e}"
        
        context += f"{idx+1}. {product_name}: {relevant_text}\n"
    
    return context

# OCR 처리 함수
def ocr_image_to_text(image):
    try:
        text = pytesseract.image_to_string(image, lang='kor')
        return clean_text(text)
    except Exception as e:
        return f"Error during OCR processing: {str(e)}"


# UI ( logo 추가 예정 )
st.title("티미룸 보험 챗봇입니다")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 컨테이너로 이미지 업로드 및 사용자 입력칸 정렬
with st.container():
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
        # 추천 약관에서 관련 문구 검색
        context = "OCR로 추출된 내용을 요약하면 다음과 같습니다.\n" + search_terms(combined_input, recommendation_results)
    
        # GPT에 질문
        assistant_response = ask_gpt(user_input, context)
    
        # 대화 상태 업데이트
        st.session_state.messages.append({"role": "user", "content": combined_input})
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    
        # 출력
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            st.markdown(assistant_response)