from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from sklearn.metrics.pairwise import cosine_similarity

from suggestion.apps import texts, index, model, generator, texts_and_filenames  # 전역 변수 불러오기

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


# 추천 이유 생성
def generate_reason_with_keywords(user_query, recommended_text, similarity_score, model, top_n=3):
    # 사용자 입력과 추천 텍스트를 단어 단위로 분리
    user_words = user_query.split()
    text_words = recommended_text.split()
    
    # 단어별 임베딩 생성
    user_embeddings = model.encode(user_words, normalize_embeddings=True)
    text_embeddings = model.encode(text_words, normalize_embeddings=True)
    
    # 유사도 계산
    similarities = cosine_similarity(user_embeddings, text_embeddings)
    
    # 유사도가 높은 단어 추출
    top_indices = similarities.max(axis=0).argsort()[-top_n:][::-1]
    keywords = [text_words[i] for i in top_indices if similarities[:, i].max() > 0.5]  # 유사도가 0.5 이상인 단어
    
    # 추천 이유 생성
    if keywords:
        reason = f"사용자 입력과 주요 키워드 ('{', '.join(keywords)}')가 연관이 있습니다. "
    else:
        reason = "사용자 입력과 연관된 명확한 키워드는 없지만 문맥적으로 유사도가 높습니다. "
    
    reason += f"텍스트와의 유사도 점수는 {similarity_score:.2f}입니다."
    return reason
    
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
            
            # 유사도 검색
            k = 3
            distances, indices = index.search(user_embedding.astype(np.float32), k)
            recommendations = [texts_and_filenames[i] for i in indices[0]]

            # RAG 기반 추천
            recommendation_results = []

            print("RAG 기반 추천 결과:")
            for i, (rec_text, rec_filename) in enumerate(recommendations):
                product_name = rec_filename  # 파일 이름을 상품명으로 사용
                similarity_score = float(distances[0][i])
                reason = generate_reason_with_keywords(user_query, rec_text, similarity_score, model)

                # 추천 결과를 딕셔너리로 저장
                recommendation = {
                    'product_name': product_name,
                    # 'rec_text': rec_text,
                    # 'summary_text': summary_text,
                    # 'similarity_score': similarity_score,
                    'reason': reason
                }
                
                recommendation_results.append(recommendation)
                
                # 출력
                print(f"추천 {i+1}: {product_name}")
                #print(f"요약: {summary_text}")
                print(f"추천 이유: {reason}")
                print("------")

            # JSON 응답 생성
            return Response({"status": "success", "recommendations": recommendation_results})

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)
