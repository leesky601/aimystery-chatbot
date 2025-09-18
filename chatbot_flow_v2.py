"""
완전히 새로운 AI 기반 챗봇 대화 시스템
new_products.json 데이터를 활용한 자연스러운 대화 생성
"""
from typing import List, Dict, Optional, Any
import random
import re
import json
from datetime import datetime
from product_manager import ProductManager
import asyncio
import httpx
from config import Config


class RealAIChatBotFlow:
    """진짜 AI 기반 대화 플로우 - 하드코딩 제로"""
    
    def __init__(self):
        self.product_manager = ProductManager()
        self.api_key = Config.FRIENDLI_TOKEN
        self.api_url = Config.FRIENDLI_BASE_URL
        self.conversation_state = {
            'turn': 0,
            'user_inputs': [],
            'bot_arguments': [],
            'current_topic': None
        }
        
        # 제품 데이터 로드
        with open('new_products.json', 'r', encoding='utf-8') as f:
            self.product_data = json.load(f)
    
    async def call_ai(self, system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
        """AI API 호출 - 실제 LLM 응답 생성"""
        if not self.api_key:
            return "API 키가 없긴해..."
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'model': Config.EXAONE_MODEL,
                'temperature': temperature,
                'max_tokens': 300
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.api_url}/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"AI 호출 오류: {e}")
        
        return "음... 그게 좋긴해!"
    
    async def generate_purchase_bot_argument(self, product_id: int, context: Dict = None) -> str:
        """구매봇의 자유로운 의견 생성"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return "제품 정보가 없긴해..."
        
        # 구매 혜택 데이터
        purchase_benefits = product.get('purchase_benefits', [])
        common_benefits = self.product_data.get('common_purchase_benefits', [])
        
        system_prompt = """당신은 LG 가전 구매를 강력히 추천하는 '박구매' 입니다.
        성격: 열정적, 확신에 찬, 경제적 관점 중시
        말투: 모든 문장을 '~긴해'로 끝냄
        
        역할:
        1. 구매의 장점을 구체적인 숫자와 함께 설명
        2. 구독의 단점을 지적
        3. 장기적 경제성 강조
        4. 소유권의 가치 강조
        """
        
        # 대화 맥락 구성
        conversation_context = ""
        if context and 'history' in context:
            recent = context['history'][-3:] if len(context['history']) > 3 else context['history']
            conversation_context = "\n최근 대화:\n" + "\n".join([f"{m['speaker']}: {m['message']}" for m in recent])
        
        user_prompt = f"""제품: {product['name']}
구매가격: {product.get('purchase_price', 0):,}원
구매 혜택: {', '.join(purchase_benefits[:3]) if purchase_benefits else '완전 소유, 중고 판매 가능'}
{conversation_context}

이 제품을 왜 구매해야 하는지 열정적으로 설명해주세요.
구체적인 가격과 혜택을 언급하며 3-4문장으로 작성하세요.
구독과 비교하여 구매가 왜 더 나은지 강조하세요."""
        
        response = await self.call_ai(system_prompt, user_prompt, 0.9)
        return response
    
    async def generate_subscription_bot_argument(self, product_id: int, context: Dict = None) -> str:
        """구독봇의 자유로운 의견 생성"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return "제품 정보가 없긴해..."
        
        # 구독 가격 계산
        subscription_prices = product.get('subscription_price', {})
        best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1] if subscription_prices else None
        
        # 구독 혜택 데이터
        subscription_benefits = product.get('subscription_benefits', [])
        common_benefits = self.product_data.get('common_subscription_benefits', [])
        
        system_prompt = """당신은 LG 가전 구독을 강력히 추천하는 '김구독' 입니다.
        성격: 친근한, 실용적, 서비스 중시
        말투: 모든 문장을 '~긴해'로 끝냄
        
        역할:
        1. 구독 가격을 말할 때 반드시 계약기간과 총액 모두 언급
        2. 케어서비스와 무상 A/S 강조
        3. 낮은 초기 비용의 장점
        4. 최신 제품으로 업그레이드 가능성
        
        중요: 가격 언급시 "6년 계약시 월 XX원, 총 72개월 XXX원" 형식 필수
        """
        
        # 대화 맥락
        conversation_context = ""
        if context and 'history' in context:
            recent = context['history'][-3:] if len(context['history']) > 3 else context['history']
            conversation_context = "\n최근 대화:\n" + "\n".join([f"{m['speaker']}: {m['message']}" for m in recent])
        
        # 할인 계산
        if subscription_prices and best_period:
            monthly = subscription_prices[best_period]
            period_years = int(best_period.replace('년', ''))
            total_months = period_years * 12
            
            # 할인 적용 (제휴카드 최대 22,000원)
            card_discount = min(22000, int(monthly * 0.2))
            final_monthly = monthly - card_discount
            
            # 멤버십 포인트 찾기
            membership_points = 0
            for benefit in subscription_benefits:
                if '멤버십' in benefit and '포인트' in benefit:
                    match = re.search(r'([\d,]+)P', benefit)
                    if match:
                        membership_points = int(match.group(1).replace(',', ''))
                        break
            
            total_price = (final_monthly * total_months) - membership_points
            
            price_info = f"""
기본: 월 {monthly:,}원
할인 후: 월 {final_monthly:,}원
{best_period} 계약시 총 {total_months}개월 {total_price:,}원
멤버십 포인트 {membership_points:,}P 적립"""
        else:
            price_info = "구독 가격 정보 없음"
        
        user_prompt = f"""제품: {product['name']}
{price_info}
구독 혜택: {', '.join(subscription_benefits[:3]) if subscription_benefits else '케어서비스, 무상 A/S'}
{conversation_context}

이 제품을 왜 구독해야 하는지 열정적으로 설명해주세요.
반드시 계약기간, 할인된 월 가격, 총액을 모두 언급하세요.
구매와 비교하여 구독이 왜 더 나은지 강조하세요."""
        
        response = await self.call_ai(system_prompt, user_prompt, 0.9)
        return response
    
    async def generate_guide_bot_question(self, product_id: int, conversation_history: List[Dict]) -> Dict:
        """안내봇의 자연스러운 질문 생성"""
        product = self.product_manager.get_product_by_id(product_id)
        
        system_prompt = """당신은 중립적인 LG 가전 상담 '안내봇'입니다.
        성격: 친절한, 중립적, 고객 중심
        말투: 모든 문장을 '~긴해'로 끝냄
        
        역할:
        1. 고객의 상황을 파악하는 핵심 질문하기
        2. 구매/구독 결정에 도움되는 정보 수집
        3. 양쪽 의견을 공평하게 정리
        """
        
        # 이전 대화에서 이미 다룬 주제 파악
        discussed_topics = set()
        for msg in conversation_history:
            text = msg.get('message', '').lower()
            if '예산' in text or '비용' in text: discussed_topics.add('budget')
            if '기간' in text or '오래' in text: discussed_topics.add('duration')
            if '서비스' in text or 'a/s' in text: discussed_topics.add('service')
            if '교체' in text or '신제품' in text: discussed_topics.add('upgrade')
        
        # 아직 안 물어본 주제 중심으로 질문 생성
        remaining_topics = []
        if 'budget' not in discussed_topics:
            remaining_topics.append("예산과 초기 비용 부담")
        if 'duration' not in discussed_topics:
            remaining_topics.append("사용 예정 기간")
        if 'service' not in discussed_topics:
            remaining_topics.append("A/S와 관리 서비스 필요성")
        if 'upgrade' not in discussed_topics:
            remaining_topics.append("신제품 교체 선호도")
        
        user_prompt = f"""제품: {product['name']}
구매가: {product.get('purchase_price', 0):,}원
구독가: 월 {list(product.get('subscription_price', {}).values())[0] if product.get('subscription_price') else 0:,}원

대화 턴: {len(conversation_history)}
아직 안 물어본 주제: {', '.join(remaining_topics) if remaining_topics else '모든 주제 다룸'}

고객에게 구매/구독 결정을 돕기 위한 핵심 질문 1개를 만드세요.
질문은 구체적이고 선택하기 쉬워야 합니다."""
        
        ai_question = await self.call_ai(system_prompt, user_prompt, 0.7)
        
        # 답변 옵션 생성
        options_prompt = f"""질문: {ai_question}

이 질문에 대한 2가지 대조적인 답변 옵션을 만드세요.
하나는 구매 성향, 하나는 구독 성향을 보여주는 답변이어야 합니다.
각 20자 이내로 간단명료하게 작성하세요.

형식:
옵션1: [구매 성향 답변]
옵션2: [구독 성향 답변]"""
        
        ai_options = await self.call_ai(system_prompt, options_prompt, 0.7)
        
        # 파싱
        suggestions = []
        for line in ai_options.split('\n'):
            if '옵션' in line and ':' in line:
                option = line.split(':', 1)[1].strip()
                if option:
                    suggestions.append(option)
        
        # 기본값
        if len(suggestions) < 2:
            suggestions = [
                "장기적으로 저렴한 게 좋아요",
                "매달 부담없이 내는 게 좋아요"
            ]
        
        suggestions.append("이제 결론을 내줘")
        
        return {
            'question': ai_question,
            'suggestions': suggestions[:3]  # 최대 3개
        }
    
    async def generate_guide_bot_conclusion(self, product_id: int, conversation_history: List[Dict]) -> str:
        """안내봇의 최종 결론 생성"""
        product = self.product_manager.get_product_by_id(product_id)
        
        # 사용자 응답 분석
        user_messages = [msg['message'] for msg in conversation_history if msg.get('speaker') == '사용자']
        
        system_prompt = """당신은 중립적인 LG 가전 상담 '안내봇'입니다.
        고객의 응답을 분석하여 구매/구독 중 최적의 선택을 추천하세요.
        
        분석 기준:
        - 예산 민감도
        - 사용 기간
        - 서비스 필요성
        - 소유 선호도
        
        말투: 모든 문장을 '~긴해'로 끝냄"""
        
        user_prompt = f"""제품: {product['name']}
구매가: {product.get('purchase_price', 0):,}원
구독가: 월 {list(product.get('subscription_price', {}).values())[0] if product.get('subscription_price') else 0:,}원

고객 응답들: {' / '.join(user_messages) if user_messages else '응답 없음'}

고객에게 최적의 선택(구매 or 구독)을 추천하고 이유를 설명하세요.
구체적인 금액과 혜택을 언급하며 3-4문장으로 결론을 내려주세요."""
        
        response = await self.call_ai(system_prompt, user_prompt, 0.7)
        return response
    
    async def generate_rebuttal(self, product_id: int, previous_message: str, speaker: str, conversation_history: List[Dict]) -> str:
        """상대방 주장에 대한 반박 생성"""
        product = self.product_manager.get_product_by_id(product_id)
        
        if speaker == "구매봇":
            system_prompt = """당신은 구매를 추천하는 '박구매'입니다.
            상대방(구독봇)의 주장에 대해 논리적으로 반박하세요.
            구매의 장점으로 반박하거나, 구독의 단점을 지적하세요.
            말투: 모든 문장을 '~긴해'로 끝냄"""
            
            benefits = product.get('purchase_benefits', [])
            context = f"구매 장점: {', '.join(benefits[:2])}" if benefits else "완전 소유, 경제성"
            
        else:  # 구독봇
            system_prompt = """당신은 구독을 추천하는 '김구독'입니다.
            상대방(구매봇)의 주장에 대해 논리적으로 반박하세요.
            구독의 장점으로 반박하거나, 구매의 단점을 지적하세요.
            말투: 모든 문장을 '~긴해'로 끝냄"""
            
            benefits = product.get('subscription_benefits', [])
            context = f"구독 장점: {', '.join(benefits[:2])}" if benefits else "케어서비스, 낮은 초기비용"
        
        user_prompt = f"""제품: {product['name']}
상대방 주장: {previous_message}
{context}

상대방 주장을 반박하세요. 2-3문장으로 간결하게.
데이터와 구체적 혜택을 근거로 사용하세요."""
        
        response = await self.call_ai(system_prompt, user_prompt, 0.8)
        return response