import requests
import re
import json
import cv2
from pdf2image import convert_from_path
import base64
import io
import os
import pandas as pd

# 클로바 OCR API 정보
CLOVA_OCR_API_URL = "https://vggh7uttkb.apigw.ntruss.com/custom/v1/36487/263ae191d733ac7399637adb69bf21b0a4219db5a4523ed65b850a6b901fe83a/general"
CLOVA_OCR_SECRET_KEY = "aGl1QmN6a1RnbFVib2F4RmVXbG1oYkR2c3ZzQ1pMRU8="

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # 불필요한 공백 제거
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣.,!?]', '', text)  # 특수문자 제거
    return text.strip()

def convert_pdf_to_image(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)
    image_path = "/tmp/output_image.jpg"
    #image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../output_image.jpg'))
    images[0].save(image_path, "JPEG")
    return image_path

def call_clova_ocr_api(image_path):
    headers = {
        'Content-Type': 'application/json',
        'X-OCR-SECRET': CLOVA_OCR_SECRET_KEY
    }
    with open(image_path, "rb") as f:
        image_data = f.read()
    data = {
        'version': 'V1',
        'requestId': 'uuid',  # 고유 요청 ID
        'timestamp': 0,
        'images': [
            {
                'format': 'jpg',
                'name': 'sample_image',
                'data': base64.b64encode(image_data).decode('utf-8')
            }
        ]
    }
    response = requests.post(CLOVA_OCR_API_URL, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        raise Exception(f"클로바 OCR 요청 실패: {response.status_code}")
    return response.json()


def extract_key_value_pairs(ocr_response, keywords, y_tolerance=55, x_tolerance=500):
    """
    특정 키워드와 그 키워드 근처의 금액을 추출합니다.
    - keywords: 찾고자 하는 키워드 목록 (예: ["진료비 총액", "공단부담 총액"])
    - y_tolerance: y축에서 키워드와 값 간 최대 거리
    - x_tolerance: x축에서 키워드와 값 간 최대 거리
    """
    fields = ocr_response["images"][0]["fields"]
    
    # 텍스트와 좌표를 정리
    texts_with_coords = [
        {
            "text": clean_text(field["inferText"]),
            "x": field["boundingPoly"]["vertices"][0]["x"],
            "y": field["boundingPoly"]["vertices"][0]["y"]
        }
        for field in fields
    ]
    # print(texts_with_coords)
    
    # 금액을 찾기 위한 정규 표현식
    amount_pattern = r'\d{1,3}(?:,\d{3})*'  # 예: 123,456 또는 789

    # 키워드와 근처 값 추출
    key_value_pairs = []
    for keyword in keywords:
        for item in texts_with_coords:
            if keyword in item["text"]:  # 키워드와 매칭
                keyword_x, keyword_y = item["x"], item["y"]
                
                # 키워드 근처 텍스트 탐색
                closest_text = None
                closest_distance = float("inf")
                
                for other_item in texts_with_coords:
                    other_x, other_y, other_text = other_item["x"], other_item["y"], other_item["text"]

                    # 거리 조건 만족 여부 확인
                    if (
                        abs(other_y - keyword_y) <= y_tolerance  # y축 거리 조건
                        and abs(other_x - keyword_x) <= x_tolerance  # x축 거리 조건
                        and other_x > keyword_x  # 키워드 오른쪽에 위치
                        and other_y > keyword_y  # other_text가 keyword 아래에 위치

                    ):
                        # 유클리드 거리 계산 (x, y 거리 기반)
                        distance = ((other_x - keyword_x)**2 + (other_y - keyword_y)**2) ** 0.5
                        
                        # 금액 형식 확인
                        if re.match(amount_pattern, other_text):
                            # 쉼표를 제거하고 숫자로 변환
                            amount = int(other_text.replace(",", ""))
                            
                            # 금액이 100 이상인 경우에만 저장
                            if amount > 100:
                                # 가장 가까운 값 중 금액 형식을 갖춘 텍스트 선택
                                if distance < closest_distance:
                                    closest_distance = distance
                                    closest_text = other_text
                                
                
                if closest_text:
                    key_value_pairs.append((item["text"], closest_text))  # 키워드와 금액 저장


    return key_value_pairs

def format_date(date_str):
    """
    날짜 문자열을 'YYYY-MM-DD' 형식으로 변환합니다.
    예: '20241030' -> '2024-10-30'
    """
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str
    
def save_to_json(data, output_path):
    """
    데이터를 JSON 파일로 저장합니다.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def clean_key(key):
    """
    키에서 숫자를 제거하여 새로운 키를 반환합니다.
    예: '6진료비총액' -> '진료비총액'
    """
    return re.sub(r'^\d+', '', key).strip()

def extract_key_value_from_pdf(pdf_path):
    image_path = convert_pdf_to_image(pdf_path)
    ocr_response = call_clova_ocr_api(image_path)
    
    # 찾고자 하는 키워드 목록
    keywords = ["진료기간", "6진료비총액", "7공단부담총액", "9이미납부한금액"]
    key_value_pairs = extract_key_value_pairs(ocr_response, keywords)
    
    # 진료기간 포맷 수정 및 데이터 정리
    cleaned_data = {}
    for key, value in key_value_pairs:
        if key == "진료기간":
            cleaned_data[clean_key(key)] = format_date(value)  # 진료기간 포맷 변경
        else:
            cleaned_data[clean_key(key)] = value  # 숫자 제거 후 저장
    
    return cleaned_data

if __name__ == "__main__":
    pdf_path = "/Users/ddinga/Downloads/진료비계산서.pdf"
    output_json_path = os.path.join(os.getcwd(), "진료비_결과.json")  # 현재 작업 디렉토리에 저장
    try:
        extracted_data = extract_key_value_from_pdf(pdf_path)
        
        # JSON 파일로 저장
        save_to_json(extracted_data, output_json_path)
        
        print("=== 키워드-값 추출 결과 ===")
        for key, value in extracted_data.items():
            print(f"{key}: {value}")
        
        print(f"\nJSON 파일로 저장 완료: {output_json_path}")
        
    except Exception as e:
        print(f"오류 발생: {e}")