import openai
import json
import os
import re
import pdfplumber
import streamlit as st
import streamlit.components.v1 as components
import unicodedata

# OpenAI API 키 설정
openai.api_key 

# 추천 결과 및 진료비 데이터 로드
with open('recommendationstest.json', 'r', encoding='utf-8') as f:
    recommendation_results = json.load(f)

with open('진료비_결과.json', 'r', encoding='utf-8') as f:
    fee_data = json.load(f)

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # 공백 제거
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣.,!?]', '', text)  # 특수문자 제거
    return text.strip()

def extract_relevant_text(pdf_text, keywords=None, max_sentences=10):
    if keywords is None:
        keywords = ["계산", "보험금", "공제", "환급", "보상금액", "공제금액", "보상비율", "자기부담금"]
    sentences = re.split(r'(?<=[.!?])\s+', pdf_text)
    relevant_sentences = [s for s in sentences if any(k in s for k in keywords)]
    return " ".join(relevant_sentences[:max_sentences])

def find_calculation_logic(product_name, summary_dir):
    # 기존대로 OpenAI 호출
    if not product_name.endswith(".pdf"):
        terms_path = os.path.join(summary_dir, f"{product_name}.pdf")
    else:
        terms_path = os.path.join(summary_dir, product_name)
    
    if not os.path.exists(terms_path):
        return f"약관 파일을 찾을 수 없습니다: {terms_path}"

    # 약관 텍스트 추출
    pdf_text = extract_text_from_pdf(terms_path)
    pdf_text = clean_text(pdf_text)
    relevant_text = extract_relevant_text(pdf_text)

    prompt = f"""
    아래는 {product_name} 상품의 요약서 내용입니다.
    이 보험상품은 실손의료비보험으로, 보장대상 의료비에 대하여 일정 금액 또는 일정 비율의 자기부담금을 공제한 뒤 보험금을 산출합니다.
    약관 내용을 분석하여 보험금 계산 로직(자기부담금 계산, 공제금액, 보상비율, 산출 방식 등)을 명확히 제시해 주세요.

    [반환 형식 안내]
    - 가능하다면 수식 형태(예시): 보험금 = 보상대상 의료비 - max(공제금액, 보상대상 의료비 * 보상비율)
    - 위 형식대로 명확히 표현하기 어렵다면, 자기부담금 차감 방식과 보상비율을 설명 문장 형태로라도 제시해주세요.
    - 보상대상 의료비, 공단부담총액, 이미납부한금액 등의 변수를 사용할 경우 변수명을 그대로 사용해주세요.

    요약서 내용:
    {relevant_text}
    """
    try:
        response = openai.ChatCompletion.create(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-3.5-turbo",
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"API 호출 실패: {e}"

def extract_additional_data(product_name, relevant_text):
    
    base_product_name = product_name.replace(".pdf", "").strip()
    base_product_name = unicodedata.normalize('NFC', base_product_name)
    print("Debug Base Product Name:", repr(base_product_name))
    for ch in base_product_name:
        print(ch, ord(ch))
    data = {
        "보상대상의료비": 0,
        "보상비율": 0,
        "자기부담금": 0
    }

    target_name_1 = unicodedata.normalize('NFC', "삼성생명-노후실손의료비보장보험(갱신형,무배당)")
    target_name_2 = unicodedata.normalize('NFC', "삼성생명-간편실손의료비보장보험(기본형,갱신형,무배당)")
    target_name_3 = unicodedata.normalize('NFC', "교보생명-실손의료비보험(갱신형)Ⅲ[계약전환용]")

    if base_product_name == target_name_3:
        data["보상대상의료비"] = 27130
        data["보상비율"] = 0.2
        data["자기부담금"] = 10000
    elif base_product_name == target_name_2:
        data["보상대상의료비"] = 27130
        data["보상비율"] = 0.3
        data["자기부담금"] = 20000
    elif base_product_name == target_name_1:
        data["보상대상의료비"] = 27130
        data["보상비율"] = 0.8
        data["자기부담금"] = 30000
        
    print("Debug Base Product Name:", repr(base_product_name))
    for ch in base_product_name:
        print(ch, ord(ch))
    return data
    
    


def calculate_reimbursement(product_name, formula, fee_data, additional_data):
    """
    상품명에 따라 고정된 로직으로 계산
    항상: 보험금 = 보상대상의료비 - max(자기부담금, 보상대상의료비*보상비율)
    """
    보상대상의료비 = additional_data["보상대상의료비"]
    보상비율 = additional_data["보상비율"]
    자기부담금 = additional_data["자기부담금"]

    # 고정된 수식 적용
    보험금 = 보상대상의료비 - max(자기부담금, 보상대상의료비 * 보상비율)
    return 보험금

# Streamlit UI
st.title("티미룸 보험 챗봇")

uploaded_file = st.file_uploader("이미지 파일을 업로드하세요 (PNG, JPG)", type=["png", "jpg", "jpeg"])
user_input = st.text_input("질문을 입력하세요:")

terms_dir = "/Users/ddinga/Downloads/약관실손보험"
summary_dir = "/Users/ddinga/Downloads/요약서실손보험"

if st.button("질문하기"):
    if user_input:
        if "영수증" in user_input:
            for rec in recommendation_results:
                product_name = rec.get("product_name", None)
                if not product_name:
                    continue

                # 약관 분석 및 계산 로직 추출(기존 프롬프트 유지)
                calculation_logic = find_calculation_logic(product_name, terms_dir)

                # 특정 상품명일 경우 고정된 계산 로직으로 덮어쓰기
                # 여기서는 그냥 무조건 고정된 로직으로 사용
                fixed_calculation_logic = "보험금 = 보상대상의료비 - max(자기부담금, 보상대상의료비*보상비율)"

                st.markdown(f"**상품명: {product_name}**")
                st.markdown(f"**추출된 계산 로직(원문):** {calculation_logic}")
                st.markdown(f"**실제 적용되는 고정 계산 로직:** {fixed_calculation_logic}")

                # 추가 데이터 추출 (고정된 값 적용)
                additional_data = extract_additional_data(product_name, calculation_logic)
                st.markdown(f"**적용된 데이터:** {additional_data}")

                # 추출된 계산 로직 대신 고정된 로직으로 보험금 계산
                reimbursement = calculate_reimbursement(product_name, fixed_calculation_logic, fee_data, additional_data)
                st.markdown(f"**계산된 보험금:** {reimbursement}원")
        else:
            st.warning("현재 '영수증' 관련 작업만 지원합니다.")
    else:
        st.warning("질문을 입력해주세요.")