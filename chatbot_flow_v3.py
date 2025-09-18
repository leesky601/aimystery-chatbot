"""
완전히 새로운 AI 기반 챗봇 대화 시스템
- 모든 하드코딩 제거
- 실제 AI API 호출로 자유로운 대화 생성
- new_products.json 데이터 기반 동적 응답
"""

import os
import json
import random
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class DynamicAIChatBotSystem:
    """완전히 동적인 AI 기반 챗봇 시스템"""
    
    def __init__(self):
        self.api_key = os.getenv("FRIENDLI_API_KEY")
        self.base_url = "https://inference.friendli.ai/v1/chat/completions"
        
        # 제품 데이터 로드
        with open('new_products.json', 'r', encoding='utf-8') as f:
            self.products_data = json.load(f)
    
    async def _call_ai_api(self, messages: List[Dict], temperature: float = 0.9, max_tokens: int = 500) -> str:
        """EXAONE API 직접 호출"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "exaone-3.5-32b-instruct",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"AI API 호출 실패: {e}")
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> str:
        """API 실패 시 기본 응답"""
        return "흠... 이 부분은 좀 더 생각해볼 필요가 있네요. 다른 관점에서 보자면..."
    
    def _get_product_info(self, product_id: int) -> Dict:
        """제품 정보 가져오기"""
        products = self.products_data.get("products", [])
        for product in products:
            if product["id"] == product_id:
                return product
        return products[0] if products else {}
    
    def _calculate_subscription_discount(self, product: Dict, period: str) -> Dict:
        """구독 할인 계산"""
        base_price = product.get('subscription_price', {}).get(period, 0)
        
        # 실제 할인 계산 로직
        discounts = {
            'affiliate_card': min(22000, base_price * 0.2),  # 제휴카드 최대 22,000원
            'membership_points': 0,  # 제품별 멤버십 포인트
            'prepayment': base_price * 0.03 if '선결제' in str(product.get('subscription_benefits', [])) else 0
        }
        
        # 멤버십 포인트 추출
        for benefit in product.get('subscription_benefits', []):
            if '멤버십 포인트' in benefit and 'P 적립' in benefit:
                try:
                    points_str = benefit.split('멤버십 포인트')[1].split('P')[0].strip()
                    points = int(''.join(filter(str.isdigit, points_str)))
                    discounts['membership_points'] = points
                except:
                    pass
        
        final_price = base_price - discounts['affiliate_card'] - discounts['prepayment']
        
        return {
            'base_price': base_price,
            'discounts': discounts,
            'final_price': final_price,
            'total_payment': final_price * int(period.replace('년', '')) * 12
        }
    
    async def generate_purchase_argument(self, product_id: int, context: Dict = None) -> str:
        """구매봇 주장 생성 - 완전히 동적"""
        product = self._get_product_info(product_id)
        
        # 대화 맥락에서 이전 발언 참고
        previous_statements = context.get('previous_statements', []) if context else []
        conversation_turn = context.get('turn', 1) if context else 1
        
        # AI에게 줄 컨텍스트 구성
        product_context = f"""
제품 정보:
- 이름: {product['name']}
- 일시불 가격: {product['purchase_price']:,}원
- 구매 혜택: {', '.join(product.get('purchase_benefits', [])[:3])}

구독 가격 (6년 기준): 월 {product.get('subscription_price', {}).get('6년', 0):,}원
총 구독 비용 (6년): {product.get('subscription_price', {}).get('6년', 0) * 72:,}원

이전 대화 내용:
{chr(10).join(previous_statements[-3:]) if previous_statements else '(첫 대화)'}
"""
        
        messages = [
            {
                "role": "system",
                "content": """당신은 LG 가전제품 구매를 강력히 권하는 판매 전문가입니다.
김원훈 스타일의 친근하고 재치있는 말투를 사용합니다 (~긴해, ~인데 말이지, ~거든요).
구독보다 구매가 더 나은 이유를 구체적인 숫자와 함께 설득력 있게 제시합니다.
이전 대화 내용을 참고하여 새로운 논점을 제시하고, 절대 같은 말을 반복하지 않습니다.
3-4문장으로 간결하고 임팩트 있게 말합니다."""
            },
            {
                "role": "user",
                "content": f"""{product_context}

대화 턴: {conversation_turn}
역할: 구매 추천 전문가

구매의 장점을 강조하면서 구독의 단점을 지적하는 설득력 있는 주장을 해주세요.
반드시 구체적인 금액과 함께 언급하고, 이전에 나온 내용과 다른 새로운 포인트를 제시하세요."""
            }
        ]
        
        response = await self._call_ai_api(messages, temperature=0.9)
        return response
    
    async def generate_subscription_argument(self, product_id: int, context: Dict = None) -> str:
        """구독봇 주장 생성 - 완전히 동적"""
        product = self._get_product_info(product_id)
        
        # 6년 기준 할인 계산
        discount_info = self._calculate_subscription_discount(product, '6년')
        
        previous_statements = context.get('previous_statements', []) if context else []
        conversation_turn = context.get('turn', 1) if context else 1
        
        product_context = f"""
제품 정보:
- 이름: {product['name']}
- 일시불 가격: {product['purchase_price']:,}원
- 구독 가격 (6년): 월 {discount_info['base_price']:,}원
- 제휴카드 할인: 월 {discount_info['discounts']['affiliate_card']:,}원
- 최종 월 구독료: {discount_info['final_price']:,}원
- 6년 총 납부액: {discount_info['total_payment']:,}원
- 구독 혜택: {', '.join(product.get('subscription_benefits', [])[:3])}

이전 대화 내용:
{chr(10).join(previous_statements[-3:]) if previous_statements else '(첫 대화)'}
"""
        
        messages = [
            {
                "role": "system",
                "content": """당신은 LG 가전제품 구독 서비스를 강력히 권하는 전문가입니다.
김원훈 스타일의 친근하고 재치있는 말투를 사용합니다 (~긴해, ~인데 말이지, ~거든요).
반드시 "6년 계약시 월 XX원이야. 총 72개월 XXX원이긴해." 형식으로 계약 기간과 총액을 언급합니다.
구독이 구매보다 더 나은 이유를 구체적인 숫자와 혜택과 함께 설득력 있게 제시합니다.
이전 대화 내용을 참고하여 새로운 논점을 제시하고, 절대 같은 말을 반복하지 않습니다.
3-4문장으로 간결하고 임팩트 있게 말합니다."""
            },
            {
                "role": "user",
                "content": f"""{product_context}

대화 턴: {conversation_turn}
역할: 구독 추천 전문가

구독의 장점을 강조하면서 구매의 단점을 지적하는 설득력 있는 주장을 해주세요.
반드시 "6년 계약시 월 {discount_info['final_price']:,}원이야. 총 72개월 {discount_info['total_payment']:,}원이긴해." 형식을 포함하고,
이전에 나온 내용과 다른 새로운 포인트를 제시하세요."""
            }
        ]
        
        response = await self._call_ai_api(messages, temperature=0.9)
        return response
    
    async def generate_dynamic_question(self, product_id: int, conversation_history: List[Dict]) -> str:
        """안내봇 질문 생성 - 완전히 동적"""
        product = self._get_product_info(product_id)
        
        # 대화 맥락 분석
        recent_topics = []
        for msg in conversation_history[-5:]:
            if msg.get('speaker') in ['구매봇', '구독봇']:
                recent_topics.append(msg.get('content', ''))
        
        # 이미 나온 질문들 추적
        asked_questions = []
        for msg in conversation_history:
            if msg.get('speaker') == '안내봇' and '?' in msg.get('content', ''):
                asked_questions.append(msg.get('content', ''))
        
        context = f"""
제품: {product['name']}
최근 논의 주제: {' / '.join(recent_topics[-3:]) if recent_topics else '없음'}
이미 했던 질문들: {' / '.join(asked_questions[-3:]) if asked_questions else '없음'}
대화 진행 정도: {len(conversation_history)}번째 대화
"""
        
        messages = [
            {
                "role": "system",
                "content": """당신은 LG 가전제품 구매 상담을 돕는 친절한 안내봇입니다.
고객이 구매와 구독 중 선택할 수 있도록 흥미로운 질문을 던집니다.
이미 했던 질문과 절대 중복되지 않는 새로운 관점의 질문을 합니다.
질문은 구체적이고 실용적이어야 하며, 고객의 실제 사용 상황과 연결되어야 합니다."""
            },
            {
                "role": "user",
                "content": f"""{context}

다음 조건을 만족하는 질문을 하나만 생성해주세요:
1. 이전에 나온 질문과 완전히 다른 새로운 관점
2. 고객이 실제로 고민할만한 실용적인 내용
3. 너무 추상적이지 않고 구체적인 상황
4. 간결하고 명확한 한 문장
5. 반드시 물음표로 끝나야 함

예시:
- "혹시 2년 후에 이사 계획이 있으신가요?"
- "가족 구성원이 늘어날 가능성은 어떠신가요?"
- "AS 센터까지의 거리가 고려사항이 되시나요?"
- "중고로 판매할 계획도 염두에 두고 계신가요?"
"""
            }
        ]
        
        response = await self._call_ai_api(messages, temperature=1.0)  # 더 창의적인 질문을 위해 temperature 높임
        return response.strip()
    
    async def respond_to_user_input(self, product_id: int, user_input: str, bot_type: str, conversation_history: List[Dict]) -> str:
        """사용자 입력에 대한 봇 응답 생성"""
        product = self._get_product_info(product_id)
        
        # 봇 타입에 따른 관점 설정
        if bot_type == '구매봇':
            perspective = "구매를 추천하는 입장"
            key_points = product.get('purchase_benefits', [])
        else:
            perspective = "구독을 추천하는 입장"
            key_points = product.get('subscription_benefits', [])
        
        context = f"""
제품: {product['name']}
사용자 입력: "{user_input}"
내 입장: {perspective}
내가 강조할 수 있는 포인트: {', '.join(key_points[:3])}
"""
        
        messages = [
            {
                "role": "system",
                "content": f"""당신은 {bot_type}입니다.
김원훈 스타일의 친근한 말투를 사용합니다 (~긴해, ~인데 말이지, ~거든요).
사용자의 질문이나 의견에 대해 {perspective}에서 답변합니다.
구체적인 숫자와 실제 혜택을 언급하며 설득력 있게 대답합니다.
2-3문장으로 간결하게 답변합니다."""
            },
            {
                "role": "user",
                "content": f"""{context}

사용자의 입력에 대해 {perspective}에서 답변해주세요.
반드시 구체적인 금액이나 혜택을 언급하고, 자연스럽고 설득력 있게 대답하세요."""
            }
        ]
        
        response = await self._call_ai_api(messages, temperature=0.8)
        return response
    
    async def generate_rebuttal(self, product_id: int, opponent_statement: str, my_bot_type: str, turn: int) -> str:
        """상대 봇의 주장에 대한 반박 생성"""
        product = self._get_product_info(product_id)
        
        if my_bot_type == '구매봇':
            my_perspective = "구매가 더 유리하다"
            my_points = product.get('purchase_benefits', [])
        else:
            my_perspective = "구독이 더 유리하다"
            my_points = product.get('subscription_benefits', [])
        
        # 대화가 진행될수록 다른 포인트 강조
        focus_point = my_points[turn % len(my_points)] if my_points else ""
        
        messages = [
            {
                "role": "system",
                "content": f"""당신은 {my_bot_type}입니다.
김원훈 스타일의 재치있는 말투를 사용합니다 (~긴해, ~인데 말이지, ~거든요).
상대방의 주장을 인정하면서도 내 입장이 더 유리함을 설득력 있게 제시합니다.
감정적이지 않고 팩트 기반으로 반박합니다."""
            },
            {
                "role": "user",
                "content": f"""상대방 주장: "{opponent_statement}"

내 입장: {my_perspective}
이번에 강조할 포인트: {focus_point}

상대방 주장을 부분적으로 인정하면서도, 내 입장이 더 유리한 이유를 설득력 있게 반박해주세요.
2-3문장으로 간결하게, 구체적인 숫자나 혜택을 언급하며 답변하세요."""
            }
        ]
        
        response = await self._call_ai_api(messages, temperature=0.85)
        return response
    
    async def generate_conclusion(self, product_id: int, conversation_history: List[Dict]) -> str:
        """최종 결론 생성"""
        product = self._get_product_info(product_id)
        
        # 대화 내용 요약
        purchase_points = []
        subscription_points = []
        
        for msg in conversation_history:
            if msg.get('speaker') == '구매봇':
                purchase_points.append(msg.get('content', ''))
            elif msg.get('speaker') == '구독봇':
                subscription_points.append(msg.get('content', ''))
        
        messages = [
            {
                "role": "system",
                "content": """당신은 공정하고 전문적인 LG 가전 상담 안내봇입니다.
양쪽의 장단점을 균형있게 정리하고, 고객의 상황에 맞는 추천을 제시합니다."""
            },
            {
                "role": "user",
                "content": f"""제품: {product['name']}

구매 측 주요 주장:
{chr(10).join(purchase_points[-3:]) if purchase_points else '없음'}

구독 측 주요 주장:
{chr(10).join(subscription_points[-3:]) if subscription_points else '없음'}

위 내용을 바탕으로 공정하고 균형잡힌 최종 결론을 제시해주세요.
1. 구매가 유리한 경우 (구체적인 상황 제시)
2. 구독이 유리한 경우 (구체적인 상황 제시)
3. 최종 추천

5-6문장으로 명확하게 정리해주세요."""
            }
        ]
        
        response = await self._call_ai_api(messages, temperature=0.7, max_tokens=800)
        return response


# 싱글톤 인스턴스
dynamic_ai_system = DynamicAIChatBotSystem()