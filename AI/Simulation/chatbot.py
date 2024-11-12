import openai

# OpenAI API 키 설정
openai.api_key = ''

# 챗봇
def chat():
    print("티미룸 보험 챗봇에 오신 것을 환영합니다! '종료'라고 입력하면 대화가 종료됩니다.")
    while True:
        # 사용자 입력
        user_input = input("사용자: ")

        if user_input.lower() == '종료':
            print("챗봇: 대화를 종료합니다. 안녕히 가세요!")
            break
    
        answer = ask_gpt(user_input)

        # 응답 출력
        if answer:
            print(f"챗봇: {answer}")
        else:
            print("챗봇: 답변을 가져올 수 없습니다. 다시 시도해 주세요.")

chat()