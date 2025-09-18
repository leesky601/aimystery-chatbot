"""
데이터 기반 제품 논쟁을 위한 추가 API 엔드포인트
"""
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import asyncio
from datetime import datetime
from product_manager import ProductManager
from chatbots import ChatBotManager

async def data_driven_product_debate(
    app,
    product_id: int,
    max_turns: int = 4,
    user_info: Optional[str] = None
):
    """데이터 기반 제품 논쟁 엔드포인트"""
    chatbot_manager = ChatBotManager()
    product_manager = ProductManager()
    
    async def generate_debate():
        try:
            # 제품 정보 확인
            product = product_manager.get_product_by_id(product_id)
            if not product:
                yield f"data: {json.dumps({'type': 'error', 'message': f'제품 ID {product_id}를 찾을 수 없습니다.'})}\n\n"
                return
            
            product_name = product.get("name", "제품")
            
            # 논쟁 시작 메시지
            yield f"data: {json.dumps({'type': 'start', 'product': product, 'message': f'데이터 기반 논쟁 시작: {product_name}'})}\n\n"
            
            # 데이터 기반 논쟁 실행
            debate_result = await chatbot_manager.start_debate_with_product(
                product_id=product_id,
                max_turns=max_turns,
                user_info=user_info
            )
            
            # 결과를 스트리밍 형태로 전송
            for idx, turn_data in enumerate(debate_result):
                speaker = turn_data.get('speaker', '')
                message = turn_data.get('message', '')
                
                # 타이핑 효과
                if speaker in ['구매봇', '구독봇']:
                    yield f"data: {json.dumps({'type': 'typing', 'speaker': speaker})}\n\n"
                    await asyncio.sleep(0.3)
                
                # 메시지 스트리밍
                chunk_size = 30
                for i in range(0, len(message), chunk_size):
                    chunk = message[i:i+chunk_size]
                    stream_data = {
                        'type': 'streaming',
                        'speaker': speaker,
                        'content': chunk
                    }
                    yield f"data: {json.dumps(stream_data)}\n\n"
                    await asyncio.sleep(0.02)
                
                # 턴 완료
                complete_data = {
                    'type': 'complete',
                    'speaker': speaker,
                    'turn': idx + 1,
                    'timestamp': turn_data.get('timestamp', datetime.now().isoformat())
                }
                yield f"data: {json.dumps(complete_data)}\n\n"
                
                # 메시지 사이 간격
                await asyncio.sleep(0.5)
            
            yield f"data: {json.dumps({'type': 'end', 'message': '데이터 기반 논쟁이 종료되었습니다.'})}\n\n"
            
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

def register_data_debate_endpoints(app):
    """데이터 기반 논쟁 엔드포인트 등록"""
    
    @app.post("/data-debate/product/{product_id}")
    async def start_data_driven_debate(
        product_id: int,
        max_turns: int = 4,
        user_info: Optional[str] = None
    ):
        """데이터 기반 제품 논쟁 시작"""
        return await data_driven_product_debate(app, product_id, max_turns, user_info)
    
    @app.get("/data-debate/test/{product_id}")
    async def test_data_debate(product_id: int):
        """데이터 기반 논쟁 테스트"""
        chatbot_manager = ChatBotManager()
        product_manager = ProductManager()
        
        try:
            # 제품 정보 확인
            product = product_manager.get_product_by_id(product_id)
            if not product:
                raise HTTPException(status_code=404, detail=f"제품 ID {product_id}를 찾을 수 없습니다.")
            
            # 간단한 테스트 논쟁 실행
            result = await chatbot_manager.start_debate_with_product(
                product_id=product_id,
                max_turns=2,
                user_info="테스트 사용자"
            )
            
            return {
                "success": True,
                "product_name": product.get("name"),
                "debate_turns": len(result),
                "debate_summary": [
                    {
                        "speaker": turn.get("speaker"),
                        "message": turn.get("message")[:100] + "..." if len(turn.get("message", "")) > 100 else turn.get("message")
                    }
                    for turn in result
                ]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"테스트 중 오류 발생: {str(e)}")