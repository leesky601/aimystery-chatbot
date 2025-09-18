"""
개선된 챗봇 대화 흐름 관리 모듈
"""
from typing import List, Dict, Optional, Any
import random
from datetime import datetime
from product_manager import ProductManager

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
        
    def get_initial_arguments(self, product_id: int) -> Dict[str, str]:
        """초기 구매/구독 전반적인 의견 생성"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return {}
        
        # 구매봇 초기 의견 (전반적인 장점)
        purchase_price = product.get('purchase_price', 0)
        purchase_argument = f"""
        {product['name']} 구매를 강력 추천합니다!
        
        첫째, {purchase_price:,}원이면 평생 소유가 가능합니다.
        둘째, 월 고정비 부담이 없어 경제적 자유를 누릴 수 있습니다.
        셋째, 필요시 중고로 판매하여 최소 {int(purchase_price * 0.5):,}원은 회수 가능합니다.
        
        구매는 완전한 소유권을 보장하는 현명한 선택입니다!
        """
        
        # 구독봇 초기 의견 (전반적인 장점)
        subscription_prices = product.get('subscription_price', {})
        if subscription_prices:
            best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
            monthly_price = subscription_prices[best_period]
            
            subscription_argument = f"""
            {product['name']} 구독을 강력 추천합니다!
            
            첫째, 월 {monthly_price:,}원으로 부담 없이 시작할 수 있습니다.
            둘째, 최대 6년간 무상 A/S와 전문 케어서비스를 받을 수 있습니다.
            셋째, LG전자 멤버십 포인트와 카드 할인 혜택까지 받을 수 있습니다.
            
            구독은 스마트한 소비의 새로운 기준입니다!
            """
        else:
            subscription_argument = "구독 서비스로 부담 없이 시작하세요!"
        
        return {
            'purchase': purchase_argument.strip(),
            'subscription': subscription_argument.strip()
        }
    
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
    
    def generate_response_to_user(self, product_id: int, user_input: str, speaker: str, conversation_history: List[Dict]) -> str:
        """사용자 답변에 대한 챗봇 응답 생성"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return "제품 정보를 찾을 수 없습니다."
        
        # 사용자 입력 분석 (70% 비중)
        user_context = self._analyze_user_input(user_input)
        
        # 대화 히스토리 분석 (30% 비중)
        history_context = self._analyze_conversation_history(conversation_history)
        
        # 스피커별 응답 생성
        if speaker == "구매봇":
            return self._generate_purchase_response(product, user_context, history_context)
        elif speaker == "구독봇":
            return self._generate_subscription_response(product, user_context, history_context)
        else:
            return "적절한 응답을 생성할 수 없습니다."
    
    def generate_rebuttal(self, product_id: int, previous_message: str, speaker: str, turn: int) -> str:
        """이전 발언에 대한 반박 생성"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return "제품 정보를 찾을 수 없습니다."
        
        # 데이터 기반 반박 시도
        data_rebuttal = self._generate_data_based_rebuttal(product, previous_message, speaker)
        
        if data_rebuttal:
            return data_rebuttal
        else:
            # 반박이 어려우면 다른 주제로 전환
            return self._generate_topic_shift(product, speaker, turn)
    
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
        """구독봇 응답 생성"""
        responses = []
        
        if user_context.get('budget_conscious'):
            monthly = self._get_best_subscription_price(product)
            responses.append(f"월 {monthly:,}원이면 부담 없이 시작할 수 있어요! 목돈 필요 없어요.")
        
        if user_context.get('service_important'):
            responses.append(f"구독하면 전문 케어서비스까지 포함이에요! A/S 걱정 없이 편하게 사용하세요.")
        
        if not responses:
            # 기본 응답
            responses.append(f"구독은 최신 트렌드! 소유보다 사용이 중요한 시대예요.")
        
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
    
    def _get_best_subscription_price(self, product: Dict) -> int:
        """최적 구독 가격 반환"""
        subscription_prices = product.get('subscription_price', {})
        if subscription_prices:
            if '6년' in subscription_prices:
                return subscription_prices['6년']
            else:
                return list(subscription_prices.values())[-1]
        return 0