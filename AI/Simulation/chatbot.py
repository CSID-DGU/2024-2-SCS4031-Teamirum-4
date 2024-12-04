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



pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../recommendations.json'))


# 추천 결과를 JSON 파일에서 불러오기
with open(pdf_dir, 'r', encoding='utf-8') as f:
    recommendation_results = json.load(f) 

# 텍스트 전처리 함수
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # 불필요한 공백 제거
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣.,!?]', '', text)  # 특수문자 제거
    return text.strip()

def create_prompt(user_input, recommendation_results):
    rag_results = []
    for rec in recommendation_results:
        try:
            rag_results.append(
                f"Rank {rec.get('rank', 'N/A')}: {rec.get('summary_text', '내용 없음')} "
                f"(상품명: {rec.get('product_name', '상품명 없음')}, "
                f"유사도 점수: {rec.get('similarity_score', 0.0):.2f})"
            )
        except KeyError as e:
            rag_results.append(f"데이터 누락: {e}")
    
    references_text = "\n".join(rag_results)

    # 시스템 메시지 생성
    system_message = (
        f"사용자의 질문과 관련된 정보를 기반으로 응답하세요.\n"
        f"다음은 관련 참고자료입니다:\n{references_text}"
    )
    return system_message

# GPT 응답 생성 함수
def ask_gpt(user_input, recommendation_results):
    
    # terms_dir = "C:/Users/kehah/Desktop/상품요약서"
    terms_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/종신보험'))
      
    
    # 시스템 메시지 생성
    system_message = create_prompt(user_input, recommendation_results)
    
    
    context = "추천된 보험상품 목록과 관련 내용입니다:\n"
    
    # RAG 결과를 명확히 구조화
    rag_results = []
    for idx, rec in enumerate(recommendation_results[:3]):
        product_name = rec.get('product_name', '상품명 없음')
        relevant_text = rec.get('relevant_text', '관련 텍스트 없음')
        similarity_score = rec.get('similarity_score', 0.0)
        rag_results.append({
            "rank" : idx+1,
            "product_name" : product_name,
            "relevant_text": relevant_text,
            "similarity_score": similarity_score,
        })
       
         # 약관 파일 처리 및 RAG 결과 보강
        for result in rag_results:
            terms_filename = result["product_name"]  # 파일 이름과 약관 파일명이 일치시켜야함
            terms_path = os.path.join(terms_dir, terms_filename)
            print(terms_path)
            relevant_text = ""
        
        if os.path.exists(terms_path):
            print('있어?')
            full_text = ""
            try:
                # 약관 파일 로드
                print('약관 파일 로드')
                if terms_path.endswith('.pdf'):
                    with pdfplumber.open(terms_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            # print(page_text)
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
                sentences = re.split(r'(?<=[.!?])\s+', full_text)[:1000]# 문장 수 제한
                
                print(full_text)

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
        
        result['relevant_text'] = relevant_text

    # GPT 메시지 포맷
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_input}
    ]

    # GPT 호출
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
# 대화 이력 관리
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 보험 전문가입니다. 사용자에게 정보를 제공합니다."}
    ]
# 파일 업로드 UI
uploaded_file = st.file_uploader("이미지 파일을 업로드하세요 (PNG, JPG)", type=["png", "jpg", "jpeg"])
user_input = st.text_input("질문을 입력하세요:")

# OCR 처리
ocr_text = ""
if uploaded_file:
    image = Image.open(uploaded_file)
    with st.spinner("이미지에서 텍스트를 추출 중..."):
        ocr_text = ocr_image_to_text(image)
    st.success("이미지에서 텍스트 추출이 완료되었습니다.")  

 # OCR 데이터 + 사용자 입력 결합
combined_input = f"{user_input.strip()} {ocr_text.strip()}".strip()

    
# 세션 상태 업데이트
if combined_input:
    assistant_response = ask_gpt(combined_input, recommendation_results)
    st.session_state.messages.append({"role": "user", "content": combined_input})
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        st.markdown(assistant_response)
else:
    st.write("질문을 입력하거나 이미지 파일을 업로드하세요.")