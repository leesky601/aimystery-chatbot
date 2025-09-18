"""
완전히 새로운 동적 AI 챗봇 API 엔드포인트 - 모든 필수 엔드포인트 포함
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import json
import os
import random
from chatbot_flow_v3 import dynamic_ai_system
from chatbots import ChatBotManager
from product_manager import ProductManager
from config import Config

app = FastAPI(
    title="동적 AI 챗봇 시스템",
    description="완전히 자유로운 AI 챗봇 대화 시스템",
    version="3.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# 전역 매니저
chatbot_manager = ChatBotManager()
product_manager = ProductManager()

@app.get("/")
async def root():
    """홈페이지 제공"""
    return FileResponse('static/index.html')

@app.get("/products")
async def get_products():
    """제품 목록 반환"""
    try:
        with open('new_products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', [])
            return {"success": True, "products": products}
    except Exception as e:
        print(f"Error loading products: {e}")
        # Fallback to product_manager if available
        try:
            products = product_manager.get_all_products()
            return {"success": True, "products": products}
        except:
            return {"success": False, "products": []}

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """특정 제품 정보 반환"""
    try:
        with open('new_products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', [])
            for product in products:
                if product['id'] == product_id:
                    return product
        raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        # Fallback to product_manager
        product = product_manager.get_product(product_id)
        if product:
            return product
        raise HTTPException(status_code=404, detail="Product not found")

class ProductDebateRequest(BaseModel):
    product_id: int
    
class UserResponseRequest(BaseModel):
    product_id: int
    user_input: str
    conversation_history: List[Dict[str, Any]]

class ChatRequest(BaseModel):
    question: str
    product_name: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []

class SingleChatResponse(BaseModel):
    response: str
    speaker: str = "안내봇"

@app.post("/chat/single", response_model=SingleChatResponse)
async def single_chat(request: ChatRequest):
    """단일 챗봇 응답 생성"""
    try:
        # 간단한 안내봇 응답
        if "안녕" in request.question or "hello" in request.question.lower():
            response = "안녕하세요! LG 가전제품 구매 상담을 도와드리겠습니다. 어떤 제품에 관심이 있으신가요?"
        elif "구독" in request.question:
            response = "구독 서비스는 초기 비용 부담을 줄이고, 전문가의 정기적인 관리를 받을 수 있는 장점이 있습니다."
        elif "구매" in request.question:
            response = "일시불 구매는 완전한 소유권을 가질 수 있고, 장기적으로 더 경제적일 수 있습니다."
        else:
            response = "제품에 대해 더 자세히 알려드릴게요. 구체적으로 어떤 점이 궁금하신가요?"
        
        return SingleChatResponse(response=response, speaker="안내봇")
    except Exception as e:
        return SingleChatResponse(
            response="죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.",
            speaker="안내봇"
        )

@app.post("/product/debate/dynamic")
async def start_dynamic_debate(request: ProductDebateRequest):
    """완전히 동적인 AI 대화 시작"""
    
    async def generate_dynamic_conversation():
        try:
            conversation_history = []
            
            # 1. 구매봇의 첫 주장 - 완전히 동적
            yield f"data: {json.dumps({'type': 'typing', 'speaker': '구매봇'})}\n\n"
            await asyncio.sleep(0.5)
            
            purchase_argument = await dynamic_ai_system.generate_purchase_argument(
                request.product_id,
                {'turn': 1, 'previous_statements': []}
            )
            conversation_history.append({'speaker': '구매봇', 'content': purchase_argument})
            
            # 스트리밍 출력
            for i in range(0, len(purchase_argument), 30):
                chunk = purchase_argument[i:i+30]
                yield f"data: {json.dumps({'type': 'streaming', 'speaker': '구매봇', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)
            
            yield f"data: {json.dumps({'type': 'complete', 'speaker': '구매봇'})}\n\n"
            
            # 2. 구독봇의 반박 - 완전히 동적
            yield f"data: {json.dumps({'type': 'typing', 'speaker': '구독봇'})}\n\n"
            await asyncio.sleep(0.5)
            
            subscription_argument = await dynamic_ai_system.generate_subscription_argument(
                request.product_id,
                {'turn': 1, 'previous_statements': [purchase_argument]}
            )
            conversation_history.append({'speaker': '구독봇', 'content': subscription_argument})
            
            for i in range(0, len(subscription_argument), 30):
                chunk = subscription_argument[i:i+30]
                yield f"data: {json.dumps({'type': 'streaming', 'speaker': '구독봇', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)
            
            yield f"data: {json.dumps({'type': 'complete', 'speaker': '구독봇'})}\n\n"
            
            # 3. 구매봇의 재반박
            yield f"data: {json.dumps({'type': 'typing', 'speaker': '구매봇'})}\n\n"
            await asyncio.sleep(0.5)
            
            purchase_rebuttal = await dynamic_ai_system.generate_rebuttal(
                request.product_id,
                subscription_argument,
                '구매봇',
                2
            )
            conversation_history.append({'speaker': '구매봇', 'content': purchase_rebuttal})
            
            for i in range(0, len(purchase_rebuttal), 30):
                chunk = purchase_rebuttal[i:i+30]
                yield f"data: {json.dumps({'type': 'streaming', 'speaker': '구매봇', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)
            
            yield f"data: {json.dumps({'type': 'complete', 'speaker': '구매봇'})}\n\n"
            
            # 4. 구독봇의 재반박
            yield f"data: {json.dumps({'type': 'typing', 'speaker': '구독봇'})}\n\n"
            await asyncio.sleep(0.5)
            
            subscription_rebuttal = await dynamic_ai_system.generate_rebuttal(
                request.product_id,
                purchase_rebuttal,
                '구독봇',
                2
            )
            conversation_history.append({'speaker': '구독봇', 'content': subscription_rebuttal})
            
            for i in range(0, len(subscription_rebuttal), 30):
                chunk = subscription_rebuttal[i:i+30]
                yield f"data: {json.dumps({'type': 'streaming', 'speaker': '구독봇', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)
            
            yield f"data: {json.dumps({'type': 'complete', 'speaker': '구독봇'})}\n\n"
            
            # 5. 안내봇의 동적 질문
            yield f"data: {json.dumps({'type': 'typing', 'speaker': '안내봇'})}\n\n"
            await asyncio.sleep(0.5)
            
            # 완전히 동적인 질문 생성
            dynamic_question = await dynamic_ai_system.generate_dynamic_question(
                request.product_id,
                conversation_history
            )
            
            # 자연스러운 인트로
            intro_phrases = [
                "오호, 둘 다 좋은 포인트가 있긴해!",
                "음... 각자 일리가 있긴해!",
                "재밌는 논쟁이긴해!",
                "고민이 되긴해!",
                "둘 다 설득력이 있긴해!"
            ]
            intro = random.choice(intro_phrases)
            full_message = f"{intro} {dynamic_question}"
            
            conversation_history.append({'speaker': '안내봇', 'content': full_message})
            
            for i in range(0, len(full_message), 30):
                chunk = full_message[i:i+30]
                yield f"data: {json.dumps({'type': 'streaming', 'speaker': '안내봇', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)
            
            # 사용자 선택 옵션 제공
            suggestions = [
                dynamic_question.replace('?', '').strip(),
                "이제 결론을 내줘"
            ]
            
            yield f"data: {json.dumps({'type': 'guide_question', 'question': dynamic_question, 'suggestions': suggestions, 'history': conversation_history})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'speaker': '안내봇'})}\n\n"
            yield f"data: {json.dumps({'type': 'waiting_user', 'message': '사용자 응답 대기 중...'})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': f'오류 발생: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_dynamic_conversation(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

# Fallback for old endpoint
@app.post("/product/debate/improved")
async def start_improved_debate_fallback(request: ProductDebateRequest):
    """이전 버전 호환을 위한 fallback"""
    return await start_dynamic_debate(request)

@app.post("/product/debate/dynamic/respond")
async def respond_to_user_dynamic(request: UserResponseRequest):
    """사용자 응답에 대한 완전히 동적인 처리"""
    
    async def generate_dynamic_response():
        try:
            # 결론 요청 처리
            if request.user_input == "이제 결론을 내줘":
                yield f"data: {json.dumps({'type': 'typing', 'speaker': '안내봇'})}\n\n"
                await asyncio.sleep(0.5)
                
                conclusion = await dynamic_ai_system.generate_conclusion(
                    request.product_id,
                    request.conversation_history
                )
                
                for i in range(0, len(conclusion), 30):
                    chunk = conclusion[i:i+30]
                    yield f"data: {json.dumps({'type': 'streaming', 'speaker': '안내봇', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.02)
                
                yield f"data: {json.dumps({'type': 'complete', 'speaker': '안내봇'})}\n\n"
                yield f"data: {json.dumps({'type': 'end', 'message': '상담이 완료되었습니다.'})}\n\n"
                return
            
            # 일반 사용자 입력 처리
            conversation_history = request.conversation_history.copy()
            conversation_history.append({'speaker': '사용자', 'content': request.user_input})
            
            # 랜덤하게 어느 봇이 먼저 응답할지 결정
            first_bot = random.choice(['구매봇', '구독봇'])
            second_bot = '구독봇' if first_bot == '구매봇' else '구매봇'
            
            # 1. 첫 번째 봇의 응답
            yield f"data: {json.dumps({'type': 'typing', 'speaker': first_bot})}\n\n"
            await asyncio.sleep(0.5)
            
            first_response = await dynamic_ai_system.respond_to_user_input(
                request.product_id,
                request.user_input,
                first_bot,
                conversation_history
            )
            conversation_history.append({'speaker': first_bot, 'content': first_response})
            
            for i in range(0, len(first_response), 30):
                chunk = first_response[i:i+30]
                yield f"data: {json.dumps({'type': 'streaming', 'speaker': first_bot, 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)
            
            yield f"data: {json.dumps({'type': 'complete', 'speaker': first_bot})}\n\n"
            
            # 2. 두 번째 봇의 반박
            yield f"data: {json.dumps({'type': 'typing', 'speaker': second_bot})}\n\n"
            await asyncio.sleep(0.5)
            
            second_response = await dynamic_ai_system.generate_rebuttal(
                request.product_id,
                first_response,
                second_bot,
                len(conversation_history)
            )
            conversation_history.append({'speaker': second_bot, 'content': second_response})
            
            for i in range(0, len(second_response), 30):
                chunk = second_response[i:i+30]
                yield f"data: {json.dumps({'type': 'streaming', 'speaker': second_bot, 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)
            
            yield f"data: {json.dumps({'type': 'complete', 'speaker': second_bot})}\n\n"
            
            # 3. 첫 번째 봇의 재반박
            yield f"data: {json.dumps({'type': 'typing', 'speaker': first_bot})}\n\n"
            await asyncio.sleep(0.5)
            
            final_rebuttal = await dynamic_ai_system.generate_rebuttal(
                request.product_id,
                second_response,
                first_bot,
                len(conversation_history)
            )
            conversation_history.append({'speaker': first_bot, 'content': final_rebuttal})
            
            for i in range(0, len(final_rebuttal), 30):
                chunk = final_rebuttal[i:i+30]
                yield f"data: {json.dumps({'type': 'streaming', 'speaker': first_bot, 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)
            
            yield f"data: {json.dumps({'type': 'complete', 'speaker': first_bot})}\n\n"
            
            # 4. 안내봇의 새로운 질문
            yield f"data: {json.dumps({'type': 'typing', 'speaker': '안내봇'})}\n\n"
            await asyncio.sleep(0.5)
            
            # 완전히 새로운 동적 질문 생성
            next_question = await dynamic_ai_system.generate_dynamic_question(
                request.product_id,
                conversation_history
            )
            
            # 자연스러운 전환 문구
            transition_phrases = [
                "흥미로운 의견들이긴해!",
                "둘 다 일리가 있긴해!",
                "좋은 포인트들이긴해!",
                "각자 장점이 있긴해!",
                "고민될만 하긴해!"
            ]
            transition = random.choice(transition_phrases)
            full_message = f"{transition} {next_question}"
            
            conversation_history.append({'speaker': '안내봇', 'content': full_message})
            
            for i in range(0, len(full_message), 30):
                chunk = full_message[i:i+30]
                yield f"data: {json.dumps({'type': 'streaming', 'speaker': '안내봇', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)
            
            # 새로운 선택 옵션
            suggestions = [
                next_question.replace('?', '').strip(),
                "이제 결론을 내줘"
            ]
            
            yield f"data: {json.dumps({'type': 'guide_question', 'question': next_question, 'suggestions': suggestions, 'history': conversation_history})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'speaker': '안내봇'})}\n\n"
            yield f"data: {json.dumps({'type': 'waiting_user', 'message': '사용자 응답 대기 중...'})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': f'오류 발생: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_dynamic_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

# Fallback for old endpoint
@app.post("/product/debate/improved/respond")
async def respond_to_user_improved_fallback(request: UserResponseRequest):
    """이전 버전 호환을 위한 fallback"""
    return await respond_to_user_dynamic(request)

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.0.0", "system": "dynamic_ai"}

@app.get("/summary")
async def get_summary():
    """대화 요약 반환"""
    return {
        "summary": "LG 가전제품 구매와 구독에 대한 상담을 진행중입니다.",
        "key_points": [
            "구매의 장점: 완전한 소유권, 장기적 경제성",
            "구독의 장점: 낮은 초기비용, 전문 관리 서비스"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)