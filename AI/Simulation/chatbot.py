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
import openai
from konlpy.tag import Okt
import unicodedata

# OpenAI API 키 설정
openai.api_key=('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')

# 추천 결과 로드
recommendationstest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../recommendations.json'))
with open(recommendationstest_path, 'r', encoding='utf-8') as f:
    recommendation_results = json.load(f)

# 카테고리 로드
recommendation_category_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../recommendations_category.json'))
with open(recommendation_category_path, 'r', encoding='utf-8') as f:
    recommendation_category = json.load(f)

# 진료비 데이터 로드
with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../진료비_결과.json')), 'r', encoding='utf-8') as f:
    fee_data = json.load(f)

# 약관, 요약서 디렉토리 설정 (필요에 맞게 경로 수정)
# terms_dir = "/Users/ddinga/Downloads/약관실손보험"
# summary_dir = "/Users/ddinga/Downloads/요약서실손보험"

pdf_summary_dirs = {
    "실손보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/실손보험')),
    "건강보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/건강보험(암 등)')),
    "종신보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/종신보험')),
    "정기보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/정기보험')),
    "기타": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품요약서/기타')),
}

pdf_full_dirs = {
    "실손보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품약관/실손보험')),
    "건강보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품약관/건강보험(암 등)')),
    "종신보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품약관/종신보험')),
    "정기보험": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품약관/정기보험')),
    "기타": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../상품약관/기타')),
}

# print(recommendation_results[0])
pdf_summary_dir = pdf_summary_dirs.get(recommendation_category[0])
pdf_full_dir = pdf_full_dirs.get(recommendation_category[0])

terms_dir = pdf_full_dir
summary_dir = pdf_summary_dir

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
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
    if not product_name.endswith(".pdf"):
        terms_path = os.path.join(summary_dir, f"{product_name}.pdf")
    else:
        terms_path = os.path.join(summary_dir, product_name)
    
    if not os.path.exists(terms_path):
        return f"약관 파일을 찾을 수 없습니다: {terms_path}"

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
            messages = [{"role": "user", "content": prompt}],
            model = "gpt-3.5-turbo",
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"API 호출 실패: {e}"

def extract_additional_data(product_name, relevant_text):
    base_product_name = product_name.replace(".pdf", "").strip()
    base_product_name = unicodedata.normalize('NFC', base_product_name)

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

    return data

def calculate_reimbursement(product_name, formula, fee_data, additional_data):
    """
    상품명에 따라 고정된 로직으로 계산
    항상: 보험금 = 보상대상의료비 - max(자기부담금, 보상대상의료비*보상비율)
    """
    보상대상의료비 = additional_data["보상대상의료비"]
    보상비율 = additional_data["보상비율"]
    자기부담금 = additional_data["자기부담금"]

    보험금 = 보상대상의료비 - max(자기부담금, 보상대상의료비 * 보상비율)
    return 보험금

# 기존 챗봇 코드 함수
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # 불필요한 공백 제거
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣.,!?]', '', text)  # 특수문자 제거
    return text.strip()

def ask_gpt(user_input, recommendation_results):
    # 영수증 또는 특정 상품명 "교보생명-실손의료비보험(갱신형)Ⅲ[계약전환용]"이 포함되면 
    # 첫 번째 로직(보험금 계산)을 적용
    if "영수증" in user_input:
        return handle_receipt_logic(recommendation_results)
    elif "실손의료비보험" in user_input:
        return handle_specific_product_logic("교보생명-실손의료비보험(갱신형)Ⅲ[계약전환용]")
    else:
        # 그렇지 않으면 기존 로직 실행
        # terms_dir = "/Users/ddinga/Downloads/약관실손보험"
        # terms_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../요약서실손보험'))
        context = "아래는 추천된 보험 상품 목록과 관련 내용입니다:\n"
        for idx, rec in enumerate(recommendation_results):
            product_name = rec.get('product_name', '상품명 없음')
            terms_filename = product_name  
            terms_path = os.path.join(terms_dir, terms_filename)
            relevant_text = ""

            if os.path.exists(terms_path):
                full_text = ""
                try:
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
                        full_text = ""
                    
                    full_text = clean_text(full_text)
                    sentences = re.split(r'(?<=[.!?])\s+', full_text)
                    sentences = sentences[:1000]
                    
                    vectorizer = TfidfVectorizer().fit(sentences + [user_input])
                    sentence_embeddings = vectorizer.transform(sentences)
                    user_embedding = vectorizer.transform([user_input])

                    similarities = cosine_similarity(user_embedding, sentence_embeddings)
                    most_similar_idx = similarities.argmax()
                    window_size = 2  # 앞뒤 2문장씩 묶는 예시 (적절히 조정 가능)
                    start_idx = max(0, most_similar_idx - window_size)
                    end_idx = min(len(sentences), most_similar_idx + window_size + 1)
                    relevant_sentences = sentences[start_idx:end_idx]
                    relevant_text = " ".join(relevant_sentences)

                except Exception as e:
                    relevant_text = "해당 상품의 약관을 처리하는 중 오류가 발생했습니다."
            else:
                relevant_text = "해당 상품의 약관을 찾을 수 없습니다."
            
            rec['relevant_text'] = relevant_text
            context += f"{idx+1}. {product_name}: {relevant_text}\n"
            print("relevant_text")

            
        messages = [
            {"role": "system", "content": "당신은 보험 상품에 대한 전문가로서 사용자에게 정보를 제공합니다. 다음은 관련 정보입니다:\n" + context},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.35,
                n=1,
                stop=None,
            )
            answer = response['choices'][0]['message']['content'].strip()
            return answer
        except Exception as e:
            return None

def handle_receipt_logic(recommendation_results):
    # "영수증" 키워드 있을 때 모든 추천상품에 대해 계산 로직 적용
    result_text = ""
    fixed_calculation_logic = "보험금 = 보상대상의료비 - max(자기부담금, 보상대상의료비*보상비율)"
    for rec in recommendation_results:
        product_name = rec.get("product_name", None)
        if not product_name:
            continue
        
        calculation_logic = find_calculation_logic(product_name, terms_dir)
        additional_data = extract_additional_data(product_name, calculation_logic)
        reimbursement = calculate_reimbursement(product_name, fixed_calculation_logic, fee_data, additional_data)

        result_text += f"**상품명: {product_name}**\n"
        result_text += f"추출된 계산 로직(원문): {calculation_logic}\n"
        result_text += f"실제 적용되는 고정 계산 로직: {fixed_calculation_logic}\n"
        result_text += f"적용된 데이터: {additional_data}\n"
        result_text += f"계산된 보험금: {reimbursement}원\n\n"
    return result_text

def handle_specific_product_logic(product_name):
    # 특정 상품명에 대해 고정된 로직 실행
    calculation_logic = find_calculation_logic(product_name, terms_dir)
    fixed_calculation_logic = "보험금 = 보상대상의료비 - max(자기부담금, 보상대상의료비*보상비율)"
    additional_data = extract_additional_data(product_name, calculation_logic)
    reimbursement = calculate_reimbursement(product_name, fixed_calculation_logic, fee_data, additional_data)

    result_text = f"**상품명: {product_name}**\n"
    result_text += f"추출된 계산 로직(원문): {calculation_logic}\n"
    result_text += f"실제 적용되는 고정 계산 로직: {fixed_calculation_logic}\n"
    result_text += f"적용된 데이터: {additional_data}\n"
    result_text += f"계산된 보험금: {reimbursement}원\n\n"
    return result_text


# 해시태그 추출 함수
def extract_hashtags(raw_content):
    okt = Okt()
    nouns = okt.nouns(raw_content)
    unique_nouns = list(set(nouns))
    hashtags = " ".join([f"#{noun}" for noun in unique_nouns])
    return hashtags

st.set_page_config(page_title="티미룸 보험 챗봇", layout="wide")

def load_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return f"<style>{f.read()}</style>"

st.markdown(load_css("styles.css"), unsafe_allow_html=True)

#유사도 내림차순
recommendation_results_sorted = sorted(
    recommendation_results,
    key=lambda x: x.get("similarity_score", 0.0),
    reverse=True
)

st.sidebar.markdown(
    """
    <div class="sidebar-container">
        <h2>추천 보험 TOP 3</h2>
    </div>
    </br>
    """,
    unsafe_allow_html=True,
)

for idx,rec in enumerate(recommendation_results):
    # 상품명과 유사도 점수 가져오기
    product_name = rec.get("product_name", "상품명 없음").replace(".pdf", "")
    similarity_score = rec.get("similarity_score", 0.0)

    # 추천 이유와 키워드 가져오기
    reason = rec.get("reason", "")
    keywords = rec.get("keywords", ["#추천이유 없음"])  # 키워드가 없을 경우 기본값 설정

    if keywords:
        hashtags = " ".join(keywords)  # 키워드를 문자열로 결합
    else:
        hashtags = "#추천이유 없음"

    # 결과 출력
    print(f"상품명: {product_name}")
    #print(f"유사도 점수: {similarity_score:.2f}")
    #print(f"추천 이유: {reason}")
    print(f"키워드: {hashtags}")
    print("-" * 30)

    # 범주화 및 신호등 색상 아이콘 설정
    if idx == 0:
        category = "매우 적합"
        icon = "🟢"  # 초록 신호등
        font_color = "black"
    elif idx < 3:
        category = "적합"
        icon = "🟠"  # 주황 신호등
        font_color = "black"
    else:
        break  # 상위 3개까지만 표시
    
    # 왼쪽 사이드바에 표시
    st.sidebar.markdown(
        f"<div style='font-size:18px; color:{font_color}; font-weight:bold;'>"
        f"<b>{product_name}</b></div>", 
        unsafe_allow_html=True
    )
    st.sidebar.markdown(f"**평가**: {icon} ({category})", unsafe_allow_html=False)

    st.sidebar.markdown(
        f"<p style = 'font-size:14px; color:gray;'>추천 이유: {hashtags}</p>",
        unsafe_allow_html=True
    )
    # 구분선 추가
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

st.sidebar.markdown(
    """
    <div class="fixed-header header-two">
        <h3>챗봇에게 물어보면 좋은 질문 LIST !</h3>
        <ul>
            <li>Q. 보험 가입 시 가장 중요한 점은?</li>
            <li>Q. 제 기준에서 해당 보험 가입시 보장 금액은 얼마나 나오나요?</li>
            <li>Q. 보험금을 보장받지 못하는 경우는 뭐가 있나요?</li>
            <li>Q. 추천받은 보험의 청구 절차가 어떻게 되나요?</li>
            <li>Q. 추천받은 보험의 보험금 지급기준이 어떻게 되나요?</li>
            <li>Q. 추천받은 보험의 해약환급금을 알려주세요</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="header">
        <h1>티미룸 보험 챗봇 👋</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="background-color: #ffffff; padding: 50px; border-radius: 10px; margin: 100px 0;">
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 보험 전문가입니다. 사용자에게 정보를 제공합니다."}
    ]

uploaded_file = st.file_uploader("이미지 파일을 업로드하세요 (PNG, JPG)", type=["png", "jpg", "jpeg"])

st.markdown(
    """
    <div style="background-color: #ffffff; padding: 5px; border-radius: 10px; margin: 5px 0;">
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    elif role == "assistant":
        with st.chat_message("assistant"):
            st.markdown(content)

user_input = st.text_input("질문을 입력하세요:")

if user_input:
    assistant_response = ask_gpt(user_input, recommendation_results)
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        st.markdown(assistant_response)
else:
    st.write("질문을 입력하거나 이미지 파일을 업로드하세요.")

#st.write("Debug: user_input =", user_input)
#st.write("Debug: messages =", st.session_state.messages)

st.markdown(
    """
    <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; margin: 20px 0;">
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="fixed-footer">
        <p>
            © 2024 티미룸 보험 챗봇 | 문의 사항은 
            <a href="mailto:contact@teamiroom.com" style="text-decoration:none; color:#007bff;">
                contact@timeroom.com
            </a>으로 연락하세요.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3, col4, col5, col6, col7, col8,col9,col10,col11,col12,col13,col14,col15,col16,col17 = st.columns(17)

image_1_path = os.path.abspath(os.path.join(os.path.dirname(__file__), './img/receipt.png'))
image_2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), './img/customer-support.png'))
image_3_path = os.path.abspath(os.path.join(os.path.dirname(__file__), './img/insurance-company.png'))
image_4_path = os.path.abspath(os.path.join(os.path.dirname(__file__), './img/qna.png'))
image_5_path = os.path.abspath(os.path.join(os.path.dirname(__file__), './img/heart.png'))
link5 = "https://pub.insure.or.kr/#fsection01"

os.path.abspath(os.path.join(os.path.dirname(__file__), './img/heart.png'))

with col3:
    st.image(image_1_path, caption="보험금 계산")

with col6:
    st.image(image_2_path, caption="고객센터 전화번호")

with col9:
    st.image(image_3_path, caption="보험사 홈페이지")

with col12:
    st.image(image_4_path, caption="자주 묻는 질문")

with col15:
    st.image(image_5_path, caption="생명보험 공시실 비교")

col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11 = st.columns(11)

with col2:
    with st.expander("보험금 정보 보기"):
        st.write("보험금 계산에 대한 상세 정보를 여기서 확인할 수 있습니다.")

with col4:
    with st.expander("고객센터"):
        st.write("4대 생명보험 고객센터 전화번호:")
        st.write("삼성생명: 1588-3114")
        st.write("한화생명: 1566-0100")
        st.write("교보생명: 1588-1001")
        st.write("신한라이프: 1588-8000")

with col6:
    with st.expander("4대 생명보험사 홈페이지 링크"):
        st.write("[삼성생명](https://www.samsunglife.com)")
        st.write("[한화생명](https://www.hanwhalife.com)")
        st.write("[교보생명](https://www.kyobo.co.kr)")
        st.write("[신한라이프](https://www.shinhanlife.co.kr)")

with col8:
    st.markdown(
        f'<a href="{link5}" target="_blank" style="text-decoration:none; font-size:16px;">👉 생명보험 공시실 바로가기</a>',
        unsafe_allow_html=True,
    )

with col10:
    st.markdown(
        f'<a href="{link5}" target="_blank" style="text-decoration:none; font-size:16px;">👉 생명보험 공시실 바로가기</a>',
        unsafe_allow_html=True,
    )
