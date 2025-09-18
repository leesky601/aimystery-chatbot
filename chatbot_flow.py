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
        """초기 구매/구독 전반적인 의견 생성 - AI를 활용한 자연스러운 응답"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return {}
        
        # 구매봇 초기 의견 
        purchase_price = product.get('purchase_price', 0)
        purchase_context = f"""
        제품: {product['name']}
        구매 가격: {purchase_price:,}원
        중고 판매 예상가: {int(purchase_price * 0.5):,}원
        """
        
        purchase_prompt = f"{product['name']} 구매의 전반적인 장점을 2-3문장으로 설명해. 김원훈 말투(~긴해)를 사용해. 가격과 소유의 장점을 강조해."
        purchase_argument = await self.generate_natural_response(purchase_prompt, purchase_context, "구매봇")
        
        # 구독봇 초기 의견 (최대 할인 적용)
        subscription_prices = product.get('subscription_price', {})
        if subscription_prices:
            best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
            price_info = self._calculate_discounted_subscription_price(product, best_period)
            
            subscription_context = f"""
            제품: {product['name']}
            {best_period} 구독 가격:
            - 기본: 월 {price_info['base_monthly']:,}원
            - 할인 적용: 월 {price_info['final_monthly']:,}원 
            - 총 {price_info['total_months']}개월 {price_info['total']:,}원
            - 할인 내역: {price_info['discount_details']}
            """
            
            subscription_prompt = f"{product['name']} 구독의 전반적인 장점을 2-3문장으로 설명해. 할인된 가격과 계약 기간, 총 금액을 포함해. 김원훈 말투(~긴해)를 사용해."
            subscription_argument = await self.generate_natural_response(subscription_prompt, subscription_context, "구독봇")
        else:
            subscription_argument = "구독이 훨씬 편하긴해! 부담 없이 시작할 수 있긴해!"
        
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
    
    def generate_guide_question(self, product_id: int, turn: int) -> Dict[str, Any]:
        """안내봇의 사용자 맞춤 질문 생성"""
        questions = [
            {
                'question': "고객님의 월 예산은 어느 정도이신가요?",
                'suggestions': [
                    "월 5만원 이하로 부담없이 사용하고 싶어요",
                    "초기 비용이 부담되지만 장기적으로 절약하고 싶어요"
                ]
            },
            {
                'question': "제품을 얼마나 오래 사용하실 계획이신가요?",
                'suggestions': [
                    "최소 5년 이상 장기간 사용할 예정이에요",
                    "2-3년 정도 사용하다가 신제품으로 교체하고 싶어요"
                ]
            },
            {
                'question': "A/S와 관리 서비스가 얼마나 중요하신가요?",
                'suggestions': [
                    "전문가 관리와 정기 점검이 꼭 필요해요",
                    "간단한 관리는 직접 할 수 있어요"
                ]
            },
            {
                'question': "제품 교체 주기를 어떻게 생각하시나요?",
                'suggestions': [
                    "한 번 사면 고장날 때까지 사용하고 싶어요",
                    "최신 기능이 나오면 교체하고 싶어요"
                ]
            },
            {
                'question': "초기 투자 비용에 대한 부담은 어느 정도인가요?",
                'suggestions': [
                    "여유 자금이 있어서 일시불 구매도 가능해요",
                    "매달 조금씩 나가는 게 부담이 적어요"
                ]
            }
        ]
        
        # 턴에 따라 다른 질문 선택
        question_index = (turn - 1) % len(questions)
        selected_question = questions[question_index]
        
        # "이제 결론을 내줘" 옵션 추가
        selected_question['suggestions'].append("이제 결론을 내줘")
        
        return selected_question
    
    async def generate_response_to_user(self, product_id: int, user_input: str, speaker: str, conversation_history: List[Dict]) -> str:
        """사용자 답변에 대한 챗봇 응답 생성"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return "제품 정보를 찾을 수 없긴해."
        
        # 사용자 입력 분석 (70% 비중)
        user_context = self._analyze_user_input(user_input)
        
        # 대화 히스토리 분석 (30% 비중)
        history_context = self._analyze_conversation_history(conversation_history)
        
        # AI를 활용한 자연스러운 응답 생성
        context = f"제품: {product['name']}\n"
        context += f"사용자 입력: {user_input}\n"
        
        if speaker == "구매봇":
            context += f"구매 가격: {product.get('purchase_price', 0):,}원\n"
            prompt = "사용자의 말에 구매가 왜 좋은지 설명해줘. 김원훈 말투(~긴해)를 사용해."
        elif speaker == "구독봇":
            subscription_prices = product.get('subscription_price', {})
            if subscription_prices:
                best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
                price_info = self._calculate_discounted_subscription_price(product, best_period)
                context += f"{best_period} 구독 (최대 할인 적용):\n"
                context += f"- 기본: 월 {price_info['base_monthly']:,}원\n"
                context += f"- 할인 후: 월 {price_info['final_monthly']:,}원\n"
                context += f"- 총 {price_info['total_months']}개월 {price_info['total']:,}원\n"
                context += f"- 할인: {price_info['discount_details']}\n"
            prompt = "사용자의 말에 구독이 왜 좋은지 설명해줘. 할인된 가격, 계약 기간, 총 금액을 모두 언급해. 김원훈 말투(~긴해)를 사용해."
        else:
            return "적절한 응답을 생성할 수 없긴해."
        
        response = await self.generate_natural_response(prompt, context, speaker)
        return response
    
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
    
    def generate_final_conclusion(self, product_id: int, conversation_history: List[Dict]) -> str:
        """안내봇의 최종 결론"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return "제품 정보를 기반으로 결론을 내릴 수 없습니다."
        
        # 대화 내용 분석
        purchase_points = 0
        subscription_points = 0
        
        for msg in conversation_history:
            if "구매" in msg.get('message', ''):
                if any(keyword in msg['message'] for keyword in ['저렴', '경제적', '소유', '중고']):
                    purchase_points += 1
            if "구독" in msg.get('message', ''):
                if any(keyword in msg['message'] for keyword in ['케어', 'A/S', '부담', '할인']):
                    subscription_points += 1
        
        # 사용자 응답 분석
        user_preferences = self._analyze_user_preferences(conversation_history)
        
        # 최종 추천
        if purchase_points > subscription_points:
            recommendation = "구매"
            reason = "장기적 경제성과 완전한 소유권"
        elif subscription_points > purchase_points:
            recommendation = "구독"
            reason = "낮은 초기 비용과 전문 관리 서비스"
        else:
            recommendation = "구매 또는 구독"
            reason = "고객님의 상황에 따라 선택"
        
        conclusion = f"""
        종합적인 분석 결과를 말씀드리겠습니다.
        
        고객님께는 **{recommendation}**을 추천드립니다.
        
        주요 이유:
        - {reason}
        - 고객님의 답변을 고려한 맞춤 추천
        
        {product['name']}의 경우:
        - 구매: {product.get('purchase_price', 0):,}원 (일시불)
        - 구독: 월 {self._get_best_subscription_price(product):,}원
        
        최종 선택은 고객님의 개인적 상황을 고려하여 결정하시기 바랍니다.
        """
        
        return conclusion.strip()
    
    # Private helper methods
    def _analyze_user_input(self, user_input: str) -> Dict:
        """사용자 입력 분석"""
        context = {
            'budget_conscious': any(word in user_input for word in ['부담', '비싸', '저렴', '예산']),
            'long_term': any(word in user_input for word in ['장기', '오래', '평생', '5년']),
            'service_important': any(word in user_input for word in ['A/S', '관리', '케어', '서비스']),
            'ownership_important': any(word in user_input for word in ['소유', '내것', '판매', '중고'])
        }
        return context
    
    def _analyze_conversation_history(self, history: List[Dict]) -> Dict:
        """대화 히스토리 분석"""
        topics = []
        for msg in history[-5:]:  # 최근 5개 메시지
            if '가격' in msg.get('message', ''):
                topics.append('price')
            if '서비스' in msg.get('message', ''):
                topics.append('service')
        return {'recent_topics': topics}
    
    def _generate_purchase_response(self, product: Dict, user_context: Dict, history_context: Dict) -> str:
        """구매봇 응답 생성"""
        responses = []
        
        if user_context.get('budget_conscious'):
            responses.append(f"초기 비용이 부담되시는 건 이해하지만, 장기적으로 보면 {product['name']} 구매가 더 경제적이에요!")
        
        if user_context.get('long_term'):
            responses.append(f"5년 이상 사용하신다면 구매가 확실히 유리해요! 구독은 5년이면 총 비용이 구매가보다 훨씬 많아져요.")
        
        if not responses:
            # 기본 응답
            purchase_price = product.get('purchase_price', 0)
            responses.append(f"{purchase_price:,}원으로 평생 소유! 이보다 확실한 투자가 어디 있겠어요?")
        
        return random.choice(responses)
    
    def _generate_subscription_response(self, product: Dict, user_context: Dict, history_context: Dict) -> str:
        """구독봇 응답 생성 - 최대 할인 적용된 가격"""
        responses = []
        subscription_prices = product.get('subscription_price', {})
        
        if subscription_prices:
            best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
            price_info = self._calculate_discounted_subscription_price(product, best_period)
            
            if user_context.get('budget_conscious'):
                responses.append(f"{best_period} 계약하면 할인 받아서 월 {price_info['final_monthly']:,}원이긴해! 총 {price_info['total']:,}원인데 {price_info['discount_details']}까지 받으면 완전 이득이긴해!")
            
            if user_context.get('service_important'):
                responses.append(f"{best_period} 구독하면 할인가 월 {price_info['final_monthly']:,}원에 케어서비스까지 포함이긴해! 총 {price_info['total']:,}원으로 A/S 걱정 없긴해!")
            
            if not responses:
                # 기본 응답
                responses.append(f"{best_period} 계약시 {price_info['discount_details']} 받아서 월 {price_info['final_monthly']:,}원이긴해! 총 {price_info['total']:,}원으로 구매보다 싸긴해!")
        else:
            responses.append("구독이 훨씬 편하긴해!")
        
        return random.choice(responses)
    
    def _generate_data_based_rebuttal(self, product: Dict, previous_message: str, speaker: str) -> Optional[str]:
        """데이터 기반 반박 생성"""
        if speaker == "구매봇":
            if "케어" in previous_message or "A/S" in previous_message:
                return f"구매해도 LG 공식 A/S는 받을 수 있어요! 게다가 {product.get('purchase_price', 0):,}원이면 훨씬 경제적이죠."
        elif speaker == "구독봇":
            if "중고" in previous_message or "판매" in previous_message:
                return "중고로 팔면 반값도 안 돼요! 구독은 항상 최신 상태로 관리받으며 사용할 수 있어요."
        return None
    
    def _generate_topic_shift(self, product: Dict, speaker: str, turn: int) -> str:
        """주제 전환 응답"""
        topics = [
            "그건 그렇고, 초기 비용 얘기를 해볼까요?",
            "아무튼 장기적인 관점에서 생각해보세요.",
            "그런데 말이죠, 요즘 트렌드를 아시나요?",
            "그보다 중요한 건 실제 사용 편의성이에요."
        ]
        return random.choice(topics)
    
    def _analyze_user_preferences(self, history: List[Dict]) -> Dict:
        """사용자 선호도 분석"""
        preferences = {
            'price_sensitive': False,
            'service_oriented': False,
            'long_term_user': False
        }
        
        for msg in history:
            if msg.get('speaker') == '사용자':
                text = msg.get('message', '')
                if '저렴' in text or '부담' in text:
                    preferences['price_sensitive'] = True
                if '서비스' in text or 'A/S' in text:
                    preferences['service_oriented'] = True
                if '장기' in text or '오래' in text:
                    preferences['long_term_user'] = True
        
        return preferences
    
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
                import re
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