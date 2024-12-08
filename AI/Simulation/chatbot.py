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
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"
 
# 추천 결과를 JSON 파일에서 불러오기
# 상대 경로로 JSON 파일 경로 설정
pdf_dir = '/Users/jjrm_mee/Desktop/2024-2-SCS4031-Teamirum-4/recommendations.json'

# 파일 존재 여부 확인
if not os.path.exists(pdf_dir):
    raise FileNotFoundError(f"File not found: {pdf_dir}")

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
    terms_dir = "/Users/jjrm_mee/Desktop/2024-2-SCS4031-Teamirum-4/상품요약서/실손보험" 
    #terms_dir = os.path.join(os.path.dirname(__file__), "상품요약서1", "실손보험")
 
    print(terms_dir)
    
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
            relevant_text = ""
        
        if os.path.exists(terms_path):
            full_text = ""
            print("있나용")
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
                sentences = re.split(r'(?<=[.!?])\s+', full_text)[:1000]# 문장 수 제한

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

    # 메시지 구성 (ChatCompletion API 형식)
    messages = [
        {"role": "system", "content": "당신은 보험 상품에 대한 전문가로서 사용자에게 정보를 제공합니다."},
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": context},
        {"role": "user", "content": "위의 정보를 바탕으로 사용자의 질문에 가장 관련 있는 답변을 제공하세요."}
    ]

    # GPT 호출
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
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

#🟢표시 :챗봇 UI
# 🟢🟢🟢🟢해시태그 추출함수
def extract_hashtags(raw_content):
    okt = Okt()
    nouns = okt.nouns(raw_content)
    unique_nouns = list(set(nouns))
    hashtags = " ".join([f"#{noun}" for noun in unique_nouns])
    return hashtags

#🟢🟢 페이지 레이아웃 설정

st.set_page_config(page_title="티미룸 보험 챗봇", layout="wide")

# CSS 파일 로드 함수
def load_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:  # 인코딩 설정
        return f"<style>{f.read()}</style>"


# CSS 파일 로드 및 적용
st.markdown(load_css("styles.css"), unsafe_allow_html=True)

#유사도 내림차순
recommendation_results_sorted = sorted(
    recommendation_results,
    key=lambda x: x.get("similarity_score", 0.0),
    reverse=True
)

# 왼쪽 사이드바: 추천 보험 TOP3
st.sidebar.markdown(
    """
    <div class="sidebar-container">
        <h2>추천 보험 TOP 3</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

# 추천 결과 출력
for idx,rec in enumerate(recommendation_results):
    product_name = rec.get("product_name", "상품명 없음").replace(".pdf", "")
    similarity_score = rec.get("similarity_score", 0.0)
    reason = rec.get("reason", "")

    # 괄호 안의 내용 추출 및 중복 제거
    if "(" in reason and ")" in reason:
        raw_content = reason[reason.find("(") + 1:reason.find(")")]  # 괄호 안 추출
        hashtags =  extract_hashtags(raw_content)
    else:
        hashtags = "#추천이유 없음"
    print("hashtags: ", hashtags)

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

# 사이드바
st.sidebar.markdown(
    """
    <div class="fixed-header header-two">
        <h3>챗봇에게 물어보면 좋은 질문 LIST !</h3>
        <ul>
            <li>Q. 보험 가입 시 가장 중요한 점은?</li>
            <li>Q. 제 기준에서 해당 보험 가입시 보장 금액은 얼마나 나오나요?</li>
            <li>Q. 보험 약관을 확인하려면 어떻게 해야 하나요?</li>
            <li>Q. 추천받은 보험의 청구 절차가 어떻게 되나요?</li>
            <li>Q. 추천받은 보험의 보험금 지급기준이 어떻게 되나요?</li>
            <li>Q. 추천받은 보험의 해약환급금을 알려주세요</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

# 🟢🟢🟢🟢**메인 영역**: 챗봇 UI
# 헤더
st.markdown(
    """
    <div class="header">
        <h1>티미룸 보험 챗봇 👋</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# 공백 추가
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# 흰색 컨테이너 생성
st.markdown(
    """
    <div style="background-color: #ffffff; padding: 50px; border-radius: 10px; margin: 100px 0;">
    </div>
    """,
    unsafe_allow_html=True,
)

# 공백 추가
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

 #🟢🟢🟢🟢 UI

# 세션 상태 초기화
# 대화 이력 관리
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 보험 전문가입니다. 사용자에게 정보를 제공합니다."}
    ]
# 파일 업로드 UI
uploaded_file = st.file_uploader("이미지 파일을 업로드하세요 (PNG, JPG)", type=["png", "jpg", "jpeg"])

#공백 추가
st.markdown(
    """
    <div style="background-color: #ffffff; padding: 5px; border-radius: 10px; margin: 5px 0;">
    </div>
    """,
    unsafe_allow_html=True,
)

# 공백 추가
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


user_input = st.text_input("질문을 입력하세요:")

# OCR 처리
ocr_text = ""
if uploaded_file:
    image = Image.open(uploaded_file)
    with st.spinner("이미지에서 텍스트를 추출 중..."):
        ocr_text = ocr_image_to_text(image)
    st.success("이미지에서 텍스트 추출이 완료되었습니다.")  

 # OCR 데이터 + 사용자 입력 결합
#combined_input = f"{user_input.strip()} {ocr_text.strip()}".strip()

    
# 세션 상태 업데이트
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
#🟢🟢🟢🟢 UI
# 흰색 컨테이너 생성
st.markdown(
    """
    <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; margin: 20px 0;">
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)



# 하단 고정 콘텐츠
st.markdown(
    """
    <div class="fixed-footer">
        <p>
            © 2024 티미룸 보험 챗봇 | 문의 사항은 
            <a href="mailto:contact@timeroom.com" style="text-decoration:none; color:#007bff;">
                contact@timeroom.com
            </a>으로 연락하세요.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


##############################################
# 13등분된 열 생성
col1, col2, col3, col4, col5, col6, col7, col8,col9,col10,col11,col12,col13,col14,col15,col16,col17 = st.columns(17)

image_1_path = "C:/Users/kehah/Desktop/2024-2-SCS4031-Teamirum-4/AI/Simulation/img/receipt.png"
image_2_path = "C:/Users/kehah/Desktop/2024-2-SCS4031-Teamirum-4/AI/Simulation/img/customer-support.png"
image_3_path = "C:/Users/kehah/Desktop/2024-2-SCS4031-Teamirum-4/AI/Simulation/img/insurance-company.png"
image_4_path = "C:/Users/kehah/Desktop/2024-2-SCS4031-Teamirum-4/AI/Simulation/img/qna.png"
image_5_path = "C:/Users/kehah/Desktop/2024-2-SCS4031-Teamirum-4/AI/Simulation/img/heart.png"
link5 = "https://pub.insure.or.kr/#fsection01"
# image_3_path = "images/image3.jpg"



# 첫 번째 열 콘텐츠
with col3:
   st.image(image_1_path, caption="보험금 계산")

# 두 번째 열 콘텐츠
with col6:
    st.image(image_2_path, caption="고객센터 전화번호")
   
# 세 번째 열 콘텐츠
with col9:
    st.image(image_3_path, caption="보험사 홈페이지")
# 4 번째 열 콘텐츠
with col12:
    st.image(image_4_path, caption="자주 묻는 질문")
# 5 번째 열 콘텐츠
with col15:
    st.image(image_5_path, caption="생명보험 공시실 비교")



##############################################
# 아래쪽 17등분된 열 생성
col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11 = st.columns(11)

# 첫 번째 콘텐츠 (2칸 차지)
with col2:
    with st.expander("보험금 정보 보기"):
        st.write("보험금 계산에 대한 상세 정보를 여기서 확인할 수 있습니다.")
        st.write("예: 보험료 계산 예시나 도구를 여기에 추가.")

# 두 번째 콘텐츠 (2칸 차지)
with col4:
    with st.expander("고객센터"):
        st.write("4대 생명보험 고객센터 전화번호:")
        st.write("삼성생명: 1588-3114")
        st.write("한화생명: 1566-0100")
        st.write("교보생명: 1588-1001")
        st.write("신한라이프: 1588-8000")

# 세 번째 콘텐츠 (2칸 차지)
with col6:
    with st.expander("4대 생명보험사 홈페이지 링크"):
        st.write("[삼성생명](https://www.samsunglife.com)")
        st.write("[한화생명](https://www.hanwhalife.com)")
        st.write("[교보생명](https://www.kyobo.co.kr)")
        st.write("[신한라이프](https://www.shinhanlife.co.kr)")

# 네 번째 콘텐츠 (2칸 차지)
with col8:
    st.markdown(
        f'<a href="{link5}" target="_blank" style="text-decoration:none; font-size:16px;">👉 생명보험 공시실 바로가기</a>',
        unsafe_allow_html=True,
    )

# 다섯 번째 콘텐츠 (2칸 차지)
with col10:
    st.markdown(
        f'<a href="{link5}" target="_blank" style="text-decoration:none; font-size:16px;">👉 생명보험 공시실 바로가기</a>',
        unsafe_allow_html=True,
    )
# 🟢🟢🟢🟢 UI끝
