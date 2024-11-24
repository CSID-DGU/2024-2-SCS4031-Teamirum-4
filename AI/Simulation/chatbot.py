import openai
import streamlit as st #설치:pip install streamlit 
from openai import OpenAI

client = OpenAI(api_key="")

#openai.api_key = st.secrets.get("", "")  # API 키는 secrets에서 가져올경우

def ask_gpt(prompt, model="gpt-3.5-turbo", messages=None):
    if messages is None:
        messages = [{"role": "user", "content": prompt}]
    else:
        messages.append({"role": "user", "content": prompt})
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        assistant_reply = response.choices[0].message.content #처리방식 변경
        return assistant_reply
    except Exception as e:
        return f"Error: {str(e)}"

# UI
st.title("티미룸 보험 챗봇")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#사용자 입력 처리
if user_input := st.chat_input("질문을 입력하세요: "):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # GPT 응답 생성
    with st.chat_message("assistant"):
        assistant_response = ask_gpt(
            prompt=user_input,
            model="gpt-3.5-turbo",
            messages=st.session_state.messages
        )
        st.markdown(assistant_response)
        
    # 메시지 히스토리에 추가
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# # 챗봇
# def chat():
#     print("티미룸 보험 챗봇에 오신 것을 환영합니다! '종료'라고 입력하면 대화가 종료됩니다.")
#     while True:
#         # 사용자 입력
#         user_input = input("사용자: ")

#         if user_input.lower() == '종료':
#             print("챗봇: 대화를 종료합니다. 안녕히 가세요!")
#             break
    
#         answer = ask_gpt(user_input)

#         # 응답 출력
#         if answer:
#             print(f"챗봇: {answer}")
#         else:
#             print("챗봇: 답변을 가져올 수 없습니다. 다시 시도해 주세요.")

# chat()