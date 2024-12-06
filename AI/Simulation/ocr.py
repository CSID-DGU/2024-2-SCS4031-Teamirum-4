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
    # image_path = "/tmp/output_image.jpg"
    image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../output_image.jpg'))
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

def parse_table_using_bounding_box(ocr_response):
    fields = ocr_response["images"][0]["fields"]
    rows = []

    # y축 기준으로 텍스트 정렬
    fields = sorted(fields, key=lambda x: x["boundingPoly"]["vertices"][0]["y"])

    current_row_y = None
    current_row = []
    for field in fields:
        y = field["boundingPoly"]["vertices"][0]["y"]
        text = clean_text(field["inferText"]) 
        if current_row_y is None or abs(y - current_row_y) < 10:  # 같은 행으로 간주
            current_row.append(text)
            current_row_y = y
        else:
            rows.append(current_row)  # 이전 행 저장
            current_row = [text]
            current_row_y = y
            
    if current_row:
        rows.append(current_row)  # 마지막 행 추가

    max_columns = max(len(row) for row in rows)
    rows = [row + [""] * (max_columns - len(row)) for row in rows]  # 열 개수 맞추기
    df = pd.DataFrame(rows)
    
    return df

def extract_medical_info(pdf_path):
    image_path = convert_pdf_to_image(pdf_path)
    ocr_response = call_clova_ocr_api(image_path)
    df = parse_table_using_bounding_box(ocr_response)
    return df

if __name__ == "__main__":
    # pdf_path = "/Users/ddinga/Downloads/진료비계산서.pdf"
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../진료비계산서.pdf'))
    try:
        table_df = extract_medical_info(pdf_path)
        
        print("=== OCR 추출 테이블 ===")
        print(table_df)
    except Exception as e:
        print(f"오류 발생: {e}")