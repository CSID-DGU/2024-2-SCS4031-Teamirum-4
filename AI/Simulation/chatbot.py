# import openai
# import streamlit as st #설치:pip install streamlit 
# from openai import OpenAI

# client = OpenAI(api_key="")

# #openai.api_key = st.secrets.get("", "")  # API 키는 secrets에서 가져올경우

# def ask_gpt(prompt, model="gpt-3.5-turbo", messages=None):
#     if messages is None:
#         messages = [{"role": "user", "content": prompt}]
#     else:
#         messages.append({"role": "user", "content": prompt})
#     try:
#         response = client.chat.completions.create(
#             model=model,
#             messages=messages
#         )
#         assistant_reply = response.choices[0].message.content #처리방식 변경
#         return assistant_reply
#     except Exception as e:
#         return f"Error: {str(e)}"

# # UI
# st.title("티미룸 보험 챗봇")

# # 세션 상태 초기화
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # 기존 메시지 표시
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# #사용자 입력 처리
# if user_input := st.chat_input("질문을 입력하세요: "):
#     st.session_state.messages.append({"role": "user", "content": user_input})
#     with st.chat_message("user"):
#         st.markdown(user_input)

#     # GPT 응답 생성
#     with st.chat_message("assistant"):
#         assistant_response = ask_gpt(
#             prompt=user_input,
#             model="gpt-3.5-turbo",
#             messages=st.session_state.messages
#         )
#         st.markdown(assistant_response)
        
#     # 메시지 히스토리에 추가
#     st.session_state.messages.append({"role": "assistant", "content": assistant_response})

import openai
from openai import OpenAI
import streamlit as st
import json
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber

# OpenAI API 키 설정
client = OpenAI(api_key="")

# 추천 결과를 JSON 파일에서 불러오기
with open('C:/Users/kehah/Desktop/2024-2-SCS4031-Teamirum-4/AI/recommendations.json', 'r', encoding='utf-8') as f:
    recommendation_results = json.load(f)

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # 불필요한 공백 제거
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣.,!?]', '', text)  # 특수문자 제거
    return text.strip()

def ask_gpt(prompt, context):

    # 메시지 구성 (ChatCompletion API 형식)
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
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 요청 중 오류 발생: {e}")
        return None
    
def search_terms(user_input, recommendation_results):
    terms_dir = "C:/Users/kehah/Desktop/상품요약서" 
    
    # 추천된 상품의 관련 내용을 수집
    context = "아래는 추천된 보험 상품 목록과 관련 내용입니다:\n"
    for idx, rec in enumerate(recommendation_results):
        product_name = rec.get('product_name', '상품명 없음')
        terms_filename = product_name  # 파일 이름과 약관 파일명이 일치시켜야함
        
        terms_path = os.path.join(terms_dir, terms_filename)
        relevant_text = ""
        
        if os.path.exists(terms_path):
            
            try:
                full_text = ""
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
    return context
    
    # ChatCompletion API 호출
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
            n=1,
            stop=None,
        )
        answer = response['choices'][0]['message']['content'].strip()
        return answer
    except Exception as e:
        print(f"OpenAI API 요청 중 오류 발생: {e}")
        return None
    
st.title("티미룸 보험 챗봇")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.text_input("질문을 입력해주세요: ")
if user_input:

    print("티미룸 보험 챗봇에 오신 것을 환영합니다!")
    
    #추천약관에서 관련문구 탐색
    context = search_terms(user_input, recommendation_results)

    # GPT 모델로 질문
    assistant_response = ask_gpt(user_input, context)

    #대화 상태 업데이트
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

    # 출력
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        st.markdown(assistant_response)

# 대화형 챗봇
# def chat():
#     while True:
#         # 사용자 입력 받기
#         user_input = input("사용자: ")

#         # '종료'를 입력하면 프로그램 종료
#         if user_input.lower() == '종료':
#             print("챗봇: 대화를 종료합니다. 안녕히 가세요!")
#             break
        
#         # GPT 모델로 질문하고 응답 받기
#         answer = ask_gpt(user_input, recommendation_results)

#         # 응답 출력
#         if answer:
#             print(f"챗봇: {answer}")
#         else:
#             print("챗봇: 답변을 가져올 수 없습니다. 다시 시도해 주세요.")

# # 챗봇 시작
# chat()