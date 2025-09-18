from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import json
import os
import httpx
import base64
from chatbots import ChatBotManager
from product_manager import ProductManager
from config import Config

app = FastAPI(
    title="챗봇 대화 시스템",
    description="두 개의 AI 챗봇이 주제에 대해 대화하는 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# 전역 매니저
chatbot_manager = ChatBotManager()
product_manager = ProductManager()

# 데이터 기반 논쟁 엔드포인트 임포트 및 등록
from api_data_debate import register_data_debate_endpoints
register_data_debate_endpoints(app)

# 요청/응답 모델
class ConversationRequest(BaseModel):
    topic: str
    max_turns: Optional[int] = 10

class DebateRequest(BaseModel):
    topic: str
    max_turns: Optional[int] = 3
    user_info: Optional[str] = None

class ProductDebateRequest(BaseModel):
    product_id: int
    max_turns: Optional[int] = 3
    user_info: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    voice: str = "echo"  # alloy, echo, fable, onyx, nova, shimmer
    speed: float = 1.7  # 음성 속도 (고정 1.5배)

class ConversationResponse(BaseModel):
    topic: str
    conversation: List[Dict[str, Any]]
    total_turns: int
    success: bool
    message: Optional[str] = None

class SingleChatRequest(BaseModel):
    message: str
    chatbot_name: str  # "알파" 또는 "베타"

class SingleChatResponse(BaseModel):
    chatbot_name: str
    response: str
    success: bool
    message: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 설정 검증"""
    try:
        Config.validate()
        print("✅ 환경변수 설정이 완료되었습니다.")
    except ValueError as e:
        print(f"❌ 환경변수 설정 오류: {e}")
        raise

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "챗봇 대화 시스템에 오신 것을 환영합니다!",
        "web_interface": "/static/index.html",
        "endpoints": {
            "start_conversation": "/conversation/start",
            "start_debate": "/debate/start",
            "debate_stream": "/debate/stream",
            "product_debate_stream": "/product/debate/stream",
            "products": "/products",
            "single_chat": "/chat/single",
            "clear_history": "/conversation/clear",
            "health": "/health"
        }
    }

@app.get("/web")
async def web_interface():
    """웹 인터페이스로 리다이렉트"""
    return FileResponse("static/index.html")

@app.post("/conversation/start", response_model=ConversationResponse)
async def start_conversation(request: ConversationRequest):
    """두 챗봇 간의 대화 시작"""
    try:
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="주제를 입력해주세요.")
        
        if request.max_turns < 1 or request.max_turns > 20:
            raise HTTPException(status_code=400, detail="대화 턴 수는 1-20 사이여야 합니다.")
        
        conversation = await chatbot_manager.start_conversation(
            topic=request.topic,
            max_turns=request.max_turns
        )
        
        return ConversationResponse(
            topic=request.topic,
            conversation=conversation,
            total_turns=len(conversation),
            success=True,
            message="대화가 성공적으로 완료되었습니다."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 시작 중 오류가 발생했습니다: {str(e)}")

@app.post("/debate/start", response_model=ConversationResponse)
async def start_debate(request: DebateRequest):
    """두 챗봇 간의 논쟁 시작 (알파: 찬성, 베타: 반대)"""
    try:
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="논쟁 주제를 입력해주세요.")
        
        if request.max_turns < 1 or request.max_turns > 20:
            raise HTTPException(status_code=400, detail="논쟁 턴 수는 1-20 사이여야 합니다.")
        
        conversation = await chatbot_manager.start_debate(
            topic=request.topic,
            max_turns=request.max_turns
        )
        
        return ConversationResponse(
            topic=request.topic,
            conversation=conversation,
            total_turns=len(conversation),
            success=True,
            message="논쟁이 성공적으로 완료되었습니다."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"논쟁 시작 중 오류가 발생했습니다: {str(e)}")

@app.post("/debate/stream")
async def start_debate_stream(request: DebateRequest):
    """실시간 스트리밍 논쟁 (3번씩 주장)"""
    async def generate_debate():
        try:
            if not request.topic.strip():
                yield f"data: {json.dumps({'error': '논쟁 주제를 입력해주세요.'})}\n\n"
                return
            
            if request.max_turns < 1 or request.max_turns > 6:
                yield f"data: {json.dumps({'error': '논쟁 턴 수는 1-6 사이여야 합니다.'})}\n\n"
                return
            
            # 논쟁 시작 메시지
            yield f"data: {json.dumps({'type': 'start', 'topic': request.topic, 'message': f'논쟁 시작: {request.topic}'})}\n\n"
            
            # 논쟁 시작 전 구매봇 타이핑 인디케이터 표시 (즉시 표시)
            yield f"data: {json.dumps({'type': 'typing', 'speaker': '구매봇'})}\n\n"
            
            # 스트리밍 논쟁 실행
            async for stream_data in chatbot_manager.start_streaming_debate(
                topic=request.topic,
                max_turns=4,  # 각자 최소 2번씩 = 총 4턴
                user_info=request.user_info
            ):
                if isinstance(stream_data, dict) and 'type' in stream_data:
                    # 스트리밍 데이터 (typing, streaming, complete)
                    yield f"data: {json.dumps(stream_data)}\n\n"
                else:
                    # 기존 턴 데이터
                    yield f"data: {json.dumps({'type': 'turn', 'data': stream_data})}\n\n"
            
            # 논쟁이 끝난 후 안내봇이 등장하도록 보장
            # 안내봇이 아직 등장하지 않았다면 강제로 등장시킴
            conversation_log = chatbot_manager.conversation_log
            if not any(msg.get('speaker') == '안내봇' for msg in conversation_log[-3:]):
                guide_message = await chatbot_manager.generate_guide_message()
                guide_turn = {
                    "turn": len(conversation_log) + 1,
                    "speaker": "안내봇",
                    "stance": "안내",
                    "message": guide_message,
                    "timestamp": chatbot_manager.get_timestamp()
                }
                yield f"data: {json.dumps({'type': 'turn', 'data': guide_turn})}\n\n"
            
            yield f"data: {json.dumps({'type': 'end', 'message': '논쟁이 종료되었습니다.'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'논쟁 중 오류 발생: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_debate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache", 
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.get("/products")
async def get_products():
    """모든 제품 목록 조회"""
    try:
        products = product_manager.get_all_products()
        return {
            "success": True,
            "products": products,
            "total": len(products)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"제품 목록 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """특정 제품 정보 조회"""
    try:
        product = product_manager.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"제품 ID {product_id}를 찾을 수 없습니다.")
        
        return {
            "success": True,
            "product": product
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"제품 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/summary")
async def get_final_summary(user_info: str = None):
    """최종 요약 및 결론 조회"""
    try:
        # 안내봇을 통해 최종 요약 생성
        guide_bot = chatbot_manager.chatbots.get('안내봇')
        if not guide_bot:
            return {"success": False, "summary": "안내봇을 찾을 수 없습니다"}
        
        # 대화 기록 가져오기
        conversation_log = chatbot_manager.get_conversation_history()
        if not conversation_log:
            return {"success": False, "summary": "대화 기록이 없습니다"}
        
        # 최근 대화 요약
        recent_messages = []
        for msg in conversation_log[-10:]:  # 최근 10개 메시지
            speaker = msg.get('speaker', '')
            message = msg.get('message', '')
            if speaker and message:
                recent_messages.append(f"{speaker}: {message[:100]}...")  # 각 메시지 100자로 제한
        
        context = "논쟁 요약:\n" + "\n".join(recent_messages)
        if user_info:
            context += f"\n\n사용자 정보: {user_info}"
        
        summary = await guide_bot.generate_response(
            "이번 논쟁을 종합적으로 정리하고 고객에게 최종 조언을 해주세요",
            context,
            debate_mode=False
        )
        
        return {"success": True, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 생성 중 오류가 발생했습니다: {str(e)}")

@app.post("/notify-budget-answered")
async def notify_budget_answered():
    """예산 질문에 답변했다는 알림"""
    try:
        # 새 ChatBotManager에는 asked_questions가 없으므로 간단히 성공 반환
        # 필요시 나중에 구현 가능
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예산 답변 알림 중 오류가 발생했습니다: {str(e)}")

class UserQARequest(BaseModel):
    question: str
    answer: str

@app.post("/user-qa")
async def save_user_qa(request: UserQARequest):
    """사용자 질문-답변 쌍 저장"""
    try:
        # 새 ChatBotManager에는 add_user_qa가 없으므로 간단히 성공 반환
        # 필요시 나중에 구현 가능
        print(f"사용자 Q&A 저장: {request.question} -> {request.answer}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 질문-답변 저장 중 오류가 발생했습니다: {str(e)}")

@app.post("/product/debate/stream")
async def start_product_debate_stream(request: ProductDebateRequest):
    """특정 제품에 대한 실시간 스트리밍 논쟁"""
    async def generate_product_debate():
        try:
            if request.max_turns < 1 or request.max_turns > 6:
                yield f"data: {json.dumps({'error': '논쟁 턴 수는 1-6 사이여야 합니다.'})}\n\n"
                return
            
            # 제품 정보 확인
            product = product_manager.get_product_by_id(request.product_id)
            if not product:
                yield f"data: {json.dumps({'error': f'제품 ID {request.product_id}를 찾을 수 없습니다.'})}\n\n"
                return
            
            # 사용자 정보에서 지원하지 않는 주기 확인 (구독 관련 문맥에서만)
            if request.user_info:
                import re
                subscription_keywords = ['구독', '계약', '월', '가격', '비용', '요금', '할래', '말래']
                exclude_keywords = ['이사', '이동', '거주', '살고', '살아', '주거', '집', '아파트']
                
                contract_pattern = r'(\d+)년'
                matches = re.findall(contract_pattern, request.user_info)
                for match in matches:
                    period = match + '년'
                    
                    # 구독 관련 키워드가 있는지 확인
                    has_subscription_keyword = any(keyword in request.user_info for keyword in subscription_keywords)
                    has_exclude_keyword = any(keyword in request.user_info for keyword in exclude_keywords)
                    
                    # 구독 관련 문맥이고 제외 키워드가 없을 때만 처리
                    if has_subscription_keyword and not has_exclude_keyword:
                        if product.get('subscription_price') and period not in product['subscription_price']:
                            # 지원하지 않는 주기에 대한 안내봇 메시지 생성
                            available_periods = list(product['subscription_price'].keys())
                            # 안내봇을 통해 메시지 생성
                            guide_bot = chatbot_manager.chatbots.get('안내봇')
                            if guide_bot:
                                guide_message = await guide_bot.generate_response(
                                    f"{period} 구독은 지원하지 않습니다. {product['name']}은 {', '.join(available_periods)} 구독만 가능합니다.",
                                    f"제품: {product['name']}\n사용자 요청 기간: {period}\n지원 기간: {', '.join(available_periods)}",
                                    debate_mode=False
                                )
                                yield f"data: {json.dumps({'type': 'guide', 'speaker': '안내봇', 'message': guide_message, 'timestamp': '00:00:00'})}\n\n"
                            return
            
            # 논쟁 시작 메시지
            product_name = product["name"]
            yield f"data: {json.dumps({'type': 'start', 'product': product, 'message': f'논쟁 시작: {product_name} - 구매 vs 구독'})}\n\n"
            
            # 논쟁 시작 전 구매봇 타이핑 인디케이터 표시 (즉시 표시)
            yield f"data: {json.dumps({'type': 'typing', 'speaker': '구매봇'})}\n\n"
            
            # 제품 기반 논쟁 실행 (새로운 데이터 기반 방식)
            debate_result = await chatbot_manager.start_debate_with_product(
                product_id=request.product_id,
                max_turns=4,  # 각자 최소 2번씩 = 총 4턴
                user_info=request.user_info
            )
            
            # 논쟁 결과를 스트리밍 형태로 전송
            for idx, turn_data in enumerate(debate_result):
                # 각 턴에 대해 타이핑 효과와 함께 전송
                speaker = turn_data.get('speaker', '')
                
                # 타이핑 인디케이터 전송 (안내봇 제외)
                if speaker in ['구매봇', '구독봇']:
                    yield f"data: {json.dumps({'type': 'typing', 'speaker': speaker})}\n\n"
                    await asyncio.sleep(0.5)  # 타이핑 효과를 위한 짧은 지연
                
                # 메시지 전송 (스트리밍 효과)
                message = turn_data.get('message', '')
                # 메시지를 청크로 나누어 전송
                chunk_size = 20  # 한 번에 전송할 문자 수
                for i in range(0, len(message), chunk_size):
                    chunk = message[i:i+chunk_size]
                    stream_data = {
                        'type': 'streaming',
                        'speaker': speaker,
                        'content': chunk
                    }
                    yield f"data: {json.dumps(stream_data)}\n\n"
                    await asyncio.sleep(0.02)  # 스트리밍 효과를 위한 지연
                
                # 턴 완료 신호
                complete_data = {
                    'type': 'complete',
                    'speaker': speaker,
                    'turn': idx + 1,
                    'timestamp': turn_data.get('timestamp', '')
                }
                yield f"data: {json.dumps(complete_data)}\n\n"
            
            # 논쟁이 끝난 후 안내봇이 등장하도록 보장
            # 안내봇이 마지막 발언자가 아니라면 확인
            conversation_log = chatbot_manager.get_conversation_history()
            if conversation_log and conversation_log[-1].get('speaker') != '안내봇':
                # 안내봇의 최종 정리 메시지 생성
                guide_bot = chatbot_manager.chatbots.get('안내봇')
                if guide_bot:
                    from datetime import datetime
                    guide_message = await guide_bot.generate_response(
                        "논쟁을 정리하고 고객에게 도움이 되는 조언을 해주세요",
                        f"제품: {product_name}\n논쟁 요약 완료",
                        debate_mode=False
                    )
                    
                    # 타이핑 효과
                    yield f"data: {json.dumps({'type': 'typing', 'speaker': '안내봇'})}\n\n"
                    await asyncio.sleep(0.5)
                    
                    # 스트리밍 전송
                    for i in range(0, len(guide_message), 20):
                        chunk = guide_message[i:i+20]
                        stream_data = {
                            'type': 'streaming',
                            'speaker': '안내봇',
                            'content': chunk
                        }
                        yield f"data: {json.dumps(stream_data)}\n\n"
                        await asyncio.sleep(0.02)
                    
                    # 완료 신호
                    complete_data = {
                        'type': 'complete',
                        'speaker': '안내봇',
                        'turn': len(conversation_log) + 1,
                        'timestamp': datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(complete_data)}\n\n"
            
            yield f"data: {json.dumps({'type': 'end', 'message': '논쟁이 종료되었습니다.'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'논쟁 중 오류 발생: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_product_debate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache", 
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.post("/chat/single", response_model=SingleChatResponse)
async def single_chat(request: SingleChatRequest):
    """개별 챗봇과의 단일 대화"""
    try:
        if request.chatbot_name not in ["알파", "베타"]:
            raise HTTPException(status_code=400, detail="챗봇 이름은 '알파' 또는 '베타'여야 합니다.")
        
        chatbot = chatbot_manager.chatbot1 if request.chatbot_name == "알파" else chatbot_manager.chatbot2
        
        response = await chatbot.generate_response(request.message)
        
        return SingleChatResponse(
            chatbot_name=request.chatbot_name,
            response=response,
            success=True,
            message="응답이 성공적으로 생성되었습니다."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"단일 대화 중 오류가 발생했습니다: {str(e)}")

@app.delete("/conversation/clear")
async def clear_conversation_history():
    """모든 대화 히스토리 초기화"""
    try:
        chatbot_manager.clear_all_history()
        return {
            "success": True,
            "message": "모든 대화 히스토리가 초기화되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"히스토리 초기화 중 오류가 발생했습니다: {str(e)}")

@app.get("/health")
async def health_check():
    """헬스 체크"""
    try:
        Config.validate()
        return {
            "status": "healthy",
            "message": "서비스가 정상적으로 작동 중입니다.",
            "config": {
                "azure_endpoint": Config.AZURE_OPENAI_ENDPOINT,
                "api_version": Config.AZURE_OPENAI_API_VERSION,
                "chatbot1_model": Config.CHATBOT_1_MODEL,
                "chatbot2_model": Config.CHATBOT_2_MODEL
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"서비스 상태 확인 중 오류: {str(e)}")

@app.get("/conversation/history")
async def get_conversation_history():
    """현재 대화 히스토리 조회"""
    conversation_log = chatbot_manager.get_conversation_history()
    return {
        "topic": "제품 구매 vs 구독 논쟁",
        "conversation_log": conversation_log,
        "total_turns": len(conversation_log)
    }

@app.post("/tts/generate")
async def generate_speech(request: TTSRequest):
    """텍스트를 음성으로 변환 (Azure OpenAI TTS 사용)"""
    try:
        # Azure OpenAI TTS API 호출
        headers = {
            "Authorization": f"Bearer {Config.AZURE_OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "tts-1",
            "input": request.text,
            "voice": request.voice,
            "speed": request.speed  # 사용자가 설정한 속도 사용
        }
        
        # Azure OpenAI TTS 엔드포인트
        tts_endpoint = f"{Config.AZURE_OPENAI_ENDPOINT}/openai/deployments/tts-1/audio/speech?api-version={Config.AZURE_OPENAI_API_VERSION}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                tts_endpoint,
                headers=headers,
                json=data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                # 오디오 데이터를 base64로 인코딩하여 반환
                audio_data = base64.b64encode(response.content).decode('utf-8')
                return {
                    "success": True,
                    "audio_data": audio_data,
                    "format": "mp3"
                }
            else:
                print(f"Azure TTS API 응답 오류: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Azure TTS API 오류: {response.text}"
                )
                
    except Exception as e:
        print(f"Azure TTS 오류 상세: {str(e)}")
        raise HTTPException(status_code=500, detail=f"음성 생성 중 오류: {str(e)}")

@app.post("/suggestions")
async def generate_suggestions(request: dict):
    """안내봇 메시지에 맞는 예상응답 생성"""
    try:
        guide_message = request.get("guide_message", "")
        user_info = request.get("user_info", "")
        
        print(f"예상응답 생성 요청 - 질문: {guide_message}, 사용자정보: {user_info}")
        
        # 환경변수 상태 확인
        print(f"AI_PROVIDER: {Config.AI_PROVIDER}")
        if Config.AI_PROVIDER == "azure":
            print(f"Azure API Key 설정됨: {bool(Config.AZURE_OPENAI_API_KEY)}")
            print(f"Azure Endpoint 설정됨: {bool(Config.AZURE_OPENAI_ENDPOINT)}")
            print(f"Azure Deployment 설정됨: {bool(Config.AZURE_OPENAI_DEPLOYMENT_NAME)}")
            print(f"Azure Deployment Name: {Config.AZURE_OPENAI_DEPLOYMENT_NAME}")
        else:
            print(f"EXAONE Token 설정됨: {bool(Config.FRIENDLI_TOKEN)}")
        
        # 안내봇 생성 (별도로 생성)
        from chatbots import ChatBot
        guide_bot = ChatBot(
            name="안내봇",
            model=Config.CHATBOT_3_MODEL,
            personality="사용자의 상황을 파악해서 구매 vs 구독 결정에 도움을 주는 친근한 안내봇",
            stance="중립"
        )
        
        suggestions = await guide_bot.generate_suggestions(guide_message, user_info)
        print(f"생성된 예상응답: {suggestions}")
        return {"suggestions": suggestions}
    except HTTPException:
        raise
    except Exception as e:
        print(f"예상응답 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"예상응답 생성 중 오류 발생: {str(e)}")

@app.post("/continue-debate")
async def continue_debate(request: dict):
    """사용자 입력 후 논쟁 계속"""
    try:
        user_input = request.get("user_input", "")
        product_id = request.get("product_id", None)
        
        if not user_input:
            raise HTTPException(status_code=400, detail="사용자 입력이 필요합니다.")
        
        if product_id is None:
            raise HTTPException(status_code=400, detail="제품 ID가 필요합니다.")
        
        # ChatBotManager 인스턴스 생성
        chatbot_manager = ChatBotManager()
        
        # 논쟁 계속
        async def generate():
            async for event in chatbot_manager.continue_debate_after_user_input(user_input, product_id):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"논쟁 계속 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"논쟁 계속 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
