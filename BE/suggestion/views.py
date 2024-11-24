from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from suggestion.apps import texts, index, model, generator  # 전역 변수 불러오기

import numpy as np
import time

# 텍스트 분할 함수
def split_text(text, max_length=512):
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 < max_length:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def json_to_query(data):
    result = []
    for category, details in data.items():
        for key, value in details.items():
            if key == '생년월일':
                birth_year, birth_month, birth_day = map(int, value.split('-'))
                result.append(f"나이: {time.localtime().tm_year - birth_year}")
            else:
                result.append(f"{key}: {value}")
    return ", ".join(result)
    
class SuggestionAPIView(APIView):
    # post로 바꿔야됨
    def post(self, request):
        try:
            # 프론트엔드에서 데이터 받기
            user_input = request.data
            # 사용자 입력 임베딩 생성
            user_query = json_to_query(user_input)
            print(user_query)
            # user_query = "50대, 질병 보장, 월 10만원"  # 사용자 입력 예시
            user_embedding = model.encode([user_query], normalize_embeddings=True)
            
            # 유사도 기반 검색
            k = 5  # 상위 5개 추천
            distances, indices = index.search(np.array(user_embedding), k)
            recommendations = [texts[i] for i in indices[0]]

            # 추천 결과 요약 생성
            response_data = []
            for rec in recommendations:
                if generator:
                    try:
                        chunks = split_text(rec, max_length=512)
                        summaries = [
                            generator(chunk, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
                            for chunk in chunks
                        ]
                        summary_text = " ".join(summaries)
                    except Exception as e:
                        summary_text = rec[:500] + "..."  # 요약 실패 시 일부 텍스트 반환
                else:
                    summary_text = rec[:500] + "..."  # 요약 모델 없을 경우 일부 텍스트 반환
                
                response_data.append(summary_text)
                
            

            # JSON 응답 생성
            return Response({"status": "success", "recommendations": response_data})

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)
