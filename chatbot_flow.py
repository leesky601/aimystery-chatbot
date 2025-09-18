"""
개선된 챗봇 대화 흐름 관리 모듈
"""
from typing import List, Dict, Optional, Any
import random
import re
from datetime import datetime
from product_manager import ProductManager
import asyncio
import httpx
from config import Config

class ImprovedChatBotFlow:
    """개선된 대화 흐름 관리 클래스"""
    
    def __init__(self):
        self.product_manager = ProductManager()
        self.conversation_state = {
            'phase': 'initial',  # initial, question, discussion, conclusion
            'turn_count': 0,
            'user_responses': [],
            'current_product_id': None,
            'discussion_topics': [],
            'last_speaker': None
        }
        self.api_key = Config.FRIENDLI_TOKEN
        self.api_url = Config.FRIENDLI_BASE_URL
        
    async def get_initial_arguments(self, product_id: int) -> Dict[str, str]:
        """초기 구매/구독 전반적인 의견 생성 - 완전 AI 기반"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return {}
        
        # 구매봇 초기 의견 - 완전 AI 생성
        purchase_benefits = product.get('purchase_benefits', [])
        purchase_context = f"""
        제품: {product['name']}
        구매 가격: {product.get('purchase_price', 0):,}원
        구매 혜택: {', '.join(purchase_benefits[:3]) if purchase_benefits else '완전 소유권, 장기적 경제성'}
        중고 판매 가능 예상가: {int(product.get('purchase_price', 0) * 0.5):,}원
        """
        
        purchase_prompt = f"""당신은 구매를 적극 추천하는 구매봇입니다. 
        {product['name']} 구매가 왜 최고의 선택인지 열정적으로 설명하세요.
        반드시 구체적인 가격과 혜택을 언급하며 3-4문장으로 작성하세요.
        김원훈 말투(모든 문장 끝에 ~긴해)를 사용하세요."""
        
        purchase_argument = await self.generate_natural_response(purchase_prompt, purchase_context, "구매봇")
        
        # 구독봇 초기 의견 - 완전 AI 생성
        subscription_prices = product.get('subscription_price', {})
        subscription_benefits = product.get('subscription_benefits', [])
        
        if subscription_prices:
            best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
            price_info = self._calculate_discounted_subscription_price(product, best_period)
            
            subscription_context = f"""
            제품: {product['name']}
            {best_period} 구독 가격:
            - 기본: 월 {price_info['base_monthly']:,}원
            - 최종 할인가: 월 {price_info['final_monthly']:,}원 
            - 총 {price_info['total_months']}개월 {price_info['total']:,}원
            - 할인 내역: {price_info['discount_details']}
            구독 혜택: {', '.join(subscription_benefits[:3]) if subscription_benefits else '케어서비스, 무상 A/S'}
            """
            
            subscription_prompt = f"""당신은 구독을 적극 추천하는 구독봇입니다.
            {product['name']} 구독이 왜 최고의 선택인지 열정적으로 설명하세요.
            반드시 {best_period} 계약, 할인된 월 가격, 총액, 혜택을 모두 언급하세요.
            김원훈 말투(모든 문장 끝에 ~긴해)를 사용하세요."""
            
            subscription_argument = await self.generate_natural_response(subscription_prompt, subscription_context, "구독봇")
        else:
            subscription_argument = await self.generate_natural_response(
                "구독 서비스의 장점을 열정적으로 설명하세요. 김원훈 말투 사용.",
                f"제품: {product['name']}",
                "구독봇"
            )
        
        return {
            'purchase': purchase_argument.strip(),
            'subscription': subscription_argument.strip()
        }
    
    async def generate_natural_response(self, prompt: str, context: str, speaker: str) -> str:
        """AI를 사용한 자연스러운 응답 생성"""
        try:
            if not self.api_key:
                # API 키가 없으면 기본 응답 사용
                return self._get_fallback_response(speaker)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            system_prompt = f"""당신은 {speaker}입니다. 
            말투 규칙: 모든 문장 끝에 '~긴해'를 붙입니다.
            예: "이게 좋긴해", "그렇긴해", "맞긴해"
            
            구독봇일 경우: 구독 가격을 말할 때 반드시 계약 기간과 총 금액을 포함해야 합니다.
            예: "6년 계약하면 월 29,000원이야. 총 72개월 동안 2,088,000원이긴해."
            
            짧고 간결하게 2-3문장으로 답변하세요."""
            
            data = {
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"{context}\n\n{prompt}"}
                ],
                'model': Config.EXAONE_MODEL,
                'temperature': 0.8,
                'max_tokens': 200
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.api_url}/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content'].strip()
        except:
            pass
        
        return self._get_fallback_response(speaker)
    
    def _get_fallback_response(self, speaker: str) -> str:
        """폴백 응답"""
        if speaker == "구매봇":
            return "구매가 확실히 이득이긴해! 내 것이 되는 게 최고긴해!"
        elif speaker == "구독봇":
            return "구독이 훨씬 편하긴해! 관리도 받고 좋긴해!"
        else:
            return "둘 다 장단점이 있긴해!"
    
    async def generate_guide_question(self, product_id: int, turn: int, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """안내봇의 사용자 맞춤 질문 생성 - AI 기반으로 개선"""
        product = self.product_manager.get_product_by_id(product_id)
        
        # 기본 질문 풀
        base_questions = [
            {
                'focus': '예산',
                'question': "고객님의 예산은 어떻게 되시나요?긴해?",
                'suggestions': [
                    "월 5만원 이하로 부담없이 사용하고 싶어요",
                    "초기 비용이 부담되지만 장기적으로 절약하고 싶어요"
                ]
            },
            {
                'focus': '사용기간',
                'question': "얼마나 오래 사용하실 계획이신가요?긴해?",
                'suggestions': [
                    "최소 5년 이상 장기간 사용할 예정이에요",
                    "2-3년 정도 사용하다가 신제품으로 교체하고 싶어요"
                ]
            },
            {
                'focus': '서비스',
                'question': "전문가 관리가 필요하신가요?긴해?",
                'suggestions': [
                    "전문가 관리와 정기 점검이 꼭 필요해요",
                    "간단한 관리는 직접 할 수 있어요"
                ]
            },
            {
                'focus': '교체주기',
                'question': "언제쯤 새 제품으로 바꾸실 생각이신가요?긴해?",
                'suggestions': [
                    "한 번 사면 고장날 때까지 사용하고 싶어요",
                    "최신 기능이 나오면 교체하고 싶어요"
                ]
            },
            {
                'focus': '초기비용',
                'question': "목돈 부담은 괜찮으신가요?긴해?",
                'suggestions': [
                    "여유 자금이 있어서 일시불 구매도 가능해요",
                    "매달 조금씩 나가는 게 부담이 적어요"
                ]
            }
        ]
        
        # 대화 맥락에 따라 적절한 질문 선택
        if conversation_history and len(conversation_history) > 2:
            # 이미 답변한 주제는 피하기
            asked_topics = []
            for msg in conversation_history:
                text = msg.get('message', '').lower()
                if '예산' in text or '비용' in text: asked_topics.append('예산')
                if '기간' in text or '오래' in text: asked_topics.append('사용기간')
                if '서비스' in text or '관리' in text: asked_topics.append('서비스')
            
            # 아직 안 물어본 질문 우선
            available_questions = [q for q in base_questions if q['focus'] not in asked_topics]
            if available_questions:
                selected_question = random.choice(available_questions)
            else:
                selected_question = random.choice(base_questions)
        else:
            # 턴 기반 기본 선택
            question_index = (turn - 1) % len(base_questions)
            selected_question = base_questions[question_index]
        
        # "이제 결론을 내줘" 옵션 추가
        result = {
            'question': selected_question['question'],
            'suggestions': selected_question['suggestions'].copy()
        }
        result['suggestions'].append("이제 결론을 내줘")
        
        return result
    
    async def generate_response_to_user(self, product_id: int, user_input: str, speaker: str, conversation_history: List[Dict]) -> str:
        """사용자 답변에 대한 챗봇 응답 생성 - 완전 AI 기반"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return await self.generate_natural_response(
                "제품 정보가 없다고 말해줘", 
                "제품 정보 없음",
                speaker
            )
        
        if speaker == "구매봇":
            return await self._generate_purchase_response(product, user_input, conversation_history)
        elif speaker == "구독봇":
            return await self._generate_subscription_response(product, user_input, conversation_history)
        else:
            # 안내봇이나 기타 응답
            context = f"""
            제품: {product['name']}
            사용자 입력: {user_input}
            대화 맥락: {' / '.join([f"{msg['speaker']}: {msg['message'][:50]}" for msg in conversation_history[-3:]])}
            """
            prompt = "사용자의 질문에 친절하고 중립적으로 답변해줘. 김원훈 말투(~긴해) 사용."
            return await self.generate_natural_response(prompt, context, speaker)
    
    async def generate_rebuttal(self, product_id: int, previous_message: str, speaker: str, turn: int) -> str:
        """이전 발언에 대한 반박 생성"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return "제품 정보를 찾을 수 없긴해."
        
        context = f"제품: {product['name']}\n"
        context += f"이전 발언: {previous_message}\n"
        
        if speaker == "구매봇":
            context += f"구매 가격: {product.get('purchase_price', 0):,}원\n"
            prompt = "이전 발언에 대해 구매가 왜 더 나은지 반박해줘. 반박이 어려우면 다른 구매 장점을 얘기해. 김원훈 말투(~긴해) 사용."
        elif speaker == "구독봇":
            subscription_prices = product.get('subscription_price', {})
            if subscription_prices:
                best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
                price_info = self._calculate_discounted_subscription_price(product, best_period)
                context += f"{best_period} 구독 (최대 할인 적용):\n"
                context += f"- 할인 후: 월 {price_info['final_monthly']:,}원 (총 {price_info['total']:,}원)\n"
                context += f"- 할인: {price_info['discount_details']}\n"
            prompt = "이전 발언에 대해 구독이 왜 더 나은지 반박해줘. 할인된 가격과 혜택 강조해. 김원훈 말투(~긴해) 사용."
        else:
            return "그렇긴해..."
        
        response = await self.generate_natural_response(prompt, context, speaker)
        return response
    
    async def generate_final_conclusion(self, product_id: int, conversation_history: List[Dict]) -> str:
        """안내봇의 최종 결론 - 완전 AI 기반"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return await self.generate_natural_response(
                "제품 정보가 없다고 안내해줘",
                "제품 정보 없음",
                "안내봇"
            )
        
        # 구독 가격 정보 계산
        subscription_prices = product.get('subscription_price', {})
        price_info = None
        if subscription_prices:
            best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
            price_info = self._calculate_discounted_subscription_price(product, best_period)
        
        # 대화 내용 요약
        user_messages = [msg['message'] for msg in conversation_history if msg.get('speaker') == '사용자']
        bot_messages = [f"{msg['speaker']}: {msg['message'][:100]}" for msg in conversation_history[-6:]]
        
        context = f"""
        제품: {product['name']}
        구매가: {product.get('purchase_price', 0):,}원
        구독가: {f"{price_info['final_monthly']:,}원/월 (총 {price_info['total']:,}원)" if price_info else '정보 없음'}
        
        사용자 답변들: {' / '.join(user_messages[-3:]) if user_messages else '없음'}
        최근 대화: {' / '.join(bot_messages)}
        """
        
        prompt = f"""당신은 중립적인 안내봇입니다.
        지금까지의 대화를 분석하여 고객에게 구매와 구독 중 무엇이 더 적합한지 최종 결론을 내려주세요.
        사용자의 답변과 선호도를 고려하여 명확한 추천을 해주세요.
        구체적인 가격과 이유를 포함하여 3-4문장으로 작성하세요.
        김원훈 말투(~긴해)를 사용하세요."""
        
        return await self.generate_natural_response(prompt, context, "안내봇")
    
    # Private helper methods
    # 분석 헬퍼 메서드들도 제거 - AI가 자체적으로 분석
    
    async def _generate_purchase_response(self, product: Dict, user_input: str, history: List[Dict]) -> str:
        """구매봇 응답 생성 - 완전 AI 기반"""
        context = f"""
        제품: {product['name']}
        구매가: {product.get('purchase_price', 0):,}원
        사용자 입력: {user_input}
        최근 대화: {' / '.join([f"{msg['speaker']}: {msg['message'][:50]}" for msg in history[-3:]])}
        """
        
        prompt = f"""당신은 구매를 추천하는 구매봇입니다.
        사용자의 입력에 대해 구매가 왜 더 나은 선택인지 설득력 있게 답변하세요.
        구체적인 가격과 장점을 언급하며 2-3문장으로 답변하세요.
        김원훈 말투(~긴해)를 반드시 사용하세요."""
        
        return await self.generate_natural_response(prompt, context, "구매봇")
    
    async def _generate_subscription_response(self, product: Dict, user_input: str, history: List[Dict]) -> str:
        """구독봇 응답 생성 - 완전 AI 기반"""
        subscription_prices = product.get('subscription_price', {})
        
        if subscription_prices:
            best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
            price_info = self._calculate_discounted_subscription_price(product, best_period)
            
            context = f"""
            제품: {product['name']}
            {best_period} 구독 할인가: 월 {price_info['final_monthly']:,}원
            총액: {price_info['total']:,}원 ({price_info['total_months']}개월)
            할인: {price_info['discount_details']}
            사용자 입력: {user_input}
            최근 대화: {' / '.join([f"{msg['speaker']}: {msg['message'][:50]}" for msg in history[-3:]])}
            """
        else:
            context = f"""
            제품: {product['name']}
            사용자 입력: {user_input}
            """
        
        prompt = f"""당신은 구독을 추천하는 구독봇입니다.
        사용자의 입력에 대해 구독이 왜 더 나은 선택인지 설득력 있게 답변하세요.
        반드시 {best_period if subscription_prices else ''} 계약 기간, 할인된 월 가격, 총액을 모두 언급하세요.
        김원훈 말투(~긴해)를 반드시 사용하세요."""
        
        return await self.generate_natural_response(prompt, context, "구독봇")
    
    # 모든 응답은 AI를 통해 동적으로 생성됨
    
    # 사용자 선호도 분석도 AI가 직접 수행
    
    def _calculate_discounted_subscription_price(self, product: Dict, period: str) -> Dict:
        """최대 할인 적용된 구독 가격 계산"""
        base_monthly_price = product.get('subscription_price', {}).get(period, 0)
        if base_monthly_price == 0:
            return {'monthly': 0, 'total': 0, 'discount_details': ''}
        
        period_years = int(period.replace('년', ''))
        total_months = period_years * 12
        
        # 1. 선결제 할인 찾기 (subscription_benefits에서)
        prepay_discount = 0
        membership_points = 0
        benefits = product.get('subscription_benefits', [])
        
        for benefit in benefits:
            if '선 결제' in benefit and '할인' in benefit:
                # "구독 요금의 30% 선 결제 시, 월 2,600원 추가 할인" 같은 패턴 파싱
                discount_match = re.search(r'월\s*([\d,]+)원\s*(?:추가\s*)?할인', benefit)
                if discount_match:
                    prepay_discount = int(discount_match.group(1).replace(',', ''))
            
            if '멤버십 포인트' in benefit and '적립' in benefit:
                # "구독 시 LG전자 멤버십 포인트 250,000P 적립됨" 같은 패턴 파싱
                points_match = re.search(r'([\d,]+)P', benefit)
                if points_match:
                    membership_points = int(points_match.group(1).replace(',', ''))
        
        # 2. 제휴 카드 할인 (최대 22,000원)
        card_discount = min(22000, int(base_monthly_price * 0.2))  # 보통 20% 정도, 최대 22,000원
        
        # 3. 최종 월 구독료 계산
        final_monthly_price = base_monthly_price - prepay_discount - card_discount
        final_monthly_price = max(0, final_monthly_price)  # 음수 방지
        
        # 4. 총 비용 계산 (멤버십 포인트는 총액에서 차감)
        total_price = (final_monthly_price * total_months) - membership_points
        
        # 할인 내역 문자열 생성
        discount_details = []
        if prepay_discount > 0:
            discount_details.append(f"선결제 할인 월 {prepay_discount:,}원")
        if card_discount > 0:
            discount_details.append(f"제휴카드 할인 월 {card_discount:,}원")
        if membership_points > 0:
            discount_details.append(f"멤버십 포인트 {membership_points:,}P 적립")
        
        return {
            'base_monthly': base_monthly_price,
            'final_monthly': final_monthly_price,
            'total': total_price,
            'total_months': total_months,
            'discount_details': ', '.join(discount_details) if discount_details else '할인 없음'
        }
    
    def _get_best_subscription_price(self, product: Dict) -> int:
        """최적 구독 가격 반환 (최대 할인 적용)"""
        subscription_prices = product.get('subscription_price', {})
        if subscription_prices:
            best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
            price_info = self._calculate_discounted_subscription_price(product, best_period)
            return price_info['final_monthly']
        return 0