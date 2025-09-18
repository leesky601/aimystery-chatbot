import json
import os
from typing import List, Dict, Optional, Tuple
import random

class ProductManager:
    def __init__(self, products_file: str = "new_products.json"):
        self.products_file = products_file
        self.products = self.load_products()
        self.penalty_info = {}
    
    def load_products(self) -> List[Dict]:
        """제품 데이터를 JSON 파일에서 로드"""
        try:
            if os.path.exists(self.products_file):
                with open(self.products_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.common_subscription_benefits = data.get('common_subscription_benefits', [])
                    self.common_purchase_benefits = data.get('common_purchase_benefits', [])
                    self.subscription_service_info = data.get('subscription_service_info', {})
                    self.penalty_info = data.get('penalty_info', {})
                    return data.get('products', [])
            else:
                self.common_subscription_benefits = []
                self.common_purchase_benefits = []
                self.subscription_service_info = {}
                self.penalty_info = {}
                return []
        except Exception as e:
            print(f"제품 데이터 로드 중 오류 발생: {e}")
            self.common_subscription_benefits = []
            self.common_purchase_benefits = []
            self.subscription_service_info = {}
            self.penalty_info = {}
            return []
    
    def save_products(self) -> bool:
        """제품 데이터를 JSON 파일에 저장"""
        try:
            data = {"products": self.products}
            with open(self.products_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"제품 데이터 저장 중 오류 발생: {e}")
            return False
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """ID로 제품 정보 조회"""
        for product in self.products:
            if product.get('id') == product_id:
                return product
        return None
    
    def get_product_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 제품 정보 조회"""
        for product in self.products:
            if product.get('name') == name:
                return product
        return None
    
    def get_all_products(self) -> List[Dict]:
        """모든 제품 정보 조회"""
        return self.products
    
    def add_product(self, product: Dict) -> bool:
        """새 제품 추가"""
        try:
            # ID 자동 할당
            if 'id' not in product:
                max_id = max([p.get('id', 0) for p in self.products], default=0)
                product['id'] = max_id + 1
            
            self.products.append(product)
            return self.save_products()
        except Exception as e:
            print(f"제품 추가 중 오류 발생: {e}")
            return False
    
    def update_product(self, product_id: int, updated_product: Dict) -> bool:
        """제품 정보 업데이트"""
        try:
            for i, product in enumerate(self.products):
                if product.get('id') == product_id:
                    updated_product['id'] = product_id
                    self.products[i] = updated_product
                    return self.save_products()
            return False
        except Exception as e:
            print(f"제품 업데이트 중 오류 발생: {e}")
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """제품 삭제"""
        try:
            self.products = [p for p in self.products if p.get('id') != product_id]
            return self.save_products()
        except Exception as e:
            print(f"제품 삭제 중 오류 발생: {e}")
            return False
    
    def get_purchase_arguments(self, product_id: int) -> List[str]:
        """구매 유도 논거 조회 (공통 + 제품별)"""
        product = self.get_product_by_id(product_id)
        if product:
            common_benefits = getattr(self, 'common_purchase_benefits', [])
            product_benefits = product.get('purchase_benefits', [])
            return common_benefits + product_benefits
        return getattr(self, 'common_purchase_benefits', [])
    
    def get_subscription_arguments(self, product_id: int) -> List[str]:
        """구독 유도 논거 조회 (공통 + 제품별)"""
        product = self.get_product_by_id(product_id)
        if product:
            common_benefits = getattr(self, 'common_subscription_benefits', [])
            product_benefits = product.get('subscription_benefits', [])
            return common_benefits + product_benefits
        return getattr(self, 'common_subscription_benefits', [])
    
    
    def get_common_subscription_benefits(self) -> List[str]:
        """공통 구독 혜택 조회"""
        return getattr(self, 'common_subscription_benefits', [])
    
    def get_common_purchase_benefits(self) -> List[str]:
        """공통 구매 혜택 조회"""
        return getattr(self, 'common_purchase_benefits', [])
    
    def get_subscription_service_info(self) -> Dict:
        """구독 서비스 정보 조회"""
        return getattr(self, 'subscription_service_info', {})
    
    def get_care_service_info(self, product_id: int) -> Optional[Dict]:
        """제품별 케어 서비스 정보 조회"""
        product = self.get_product_by_id(product_id)
        if product:
            return product.get('care_service', {})
        return None
    
    def get_contract_periods(self, product_id: int) -> List[str]:
        """제품별 계약 주기 조회"""
        product = self.get_product_by_id(product_id)
        if product:
            return product.get('contract_periods', [])
        return []
    
    def get_penalty_info(self) -> Dict:
        """위약금 정보 조회"""
        return self.penalty_info
    
    def calculate_total_cost(self, product_id: int, period: str, is_subscription: bool) -> Tuple[int, str]:
        """총 비용 계산 및 상세 내역 반환"""
        product = self.get_product_by_id(product_id)
        if not product:
            return 0, "제품 정보를 찾을 수 없습니다"
        
        if is_subscription:
            # 구독 비용 계산
            subscription_prices = product.get('subscription_price', {})
            if period in subscription_prices:
                monthly_price = subscription_prices[period]
                months = int(period.replace('년', '')) * 12
                total = monthly_price * months
                
                # 케어서비스 비용 추가 (있는 경우)
                care_price = product.get('care_service_price', {})
                if isinstance(care_price, dict) and 'subscription' in care_price:
                    if period in care_price['subscription']:
                        # 기본 케어서비스 비용 (방문없음/자가관리 기준)
                        care_monthly = care_price['subscription'][period].get('방문없음/자가관리', 0)
                        total += care_monthly * months
                        return total, f"월 {monthly_price:,}원 x {months}개월 + 케어서비스 월 {care_monthly:,}원 = 총 {total:,}원"
                
                return total, f"월 {monthly_price:,}원 x {months}개월 = 총 {total:,}원"
            return 0, "해당 기간의 구독 가격 정보가 없습니다"
        else:
            # 구매 비용
            purchase_price = product.get('purchase_price', 0)
            return purchase_price, f"일시불 구매 가격: {purchase_price:,}원"
    
    def get_specific_benefit_data(self, product_id: int, stance: str) -> List[str]:
        """특정 제품의 구체적인 혜택 데이터 추출"""
        product = self.get_product_by_id(product_id)
        if not product:
            return []
        
        benefits = []
        
        if stance == "구매":
            # 구매 가격 정보
            purchase_price = product.get('purchase_price', 0)
            benefits.append(f"일시불 {purchase_price:,}원으로 평생 소유")
            
            # 구매만의 특별 혜택
            purchase_benefits = product.get('purchase_benefits', [])
            if purchase_benefits:
                # 랜덤하게 2-3개 선택
                selected = random.sample(purchase_benefits, min(3, len(purchase_benefits)))
                benefits.extend(selected)
            
            # 중고 판매 가능성 강조
            if purchase_price > 1000000:
                resale_value = int(purchase_price * 0.6)  # 예상 중고가 60%
                benefits.append(f"나중에 중고로 팔면 약 {resale_value:,}원 회수 가능")
            
        else:  # 구독
            # 구독 가격 정보
            subscription_prices = product.get('subscription_price', {})
            if subscription_prices:
                # 가장 인기 있는 기간 선택 (보통 5-6년)
                best_period = '6년' if '6년' in subscription_prices else list(subscription_prices.keys())[-1]
                monthly_price = subscription_prices[best_period]
                benefits.append(f"{best_period} 구독 시 월 {monthly_price:,}원")
            
            # 구독만의 특별 혜택
            subscription_benefits = product.get('subscription_benefits', [])
            if subscription_benefits:
                # 랜덤하게 2-3개 선택
                selected = random.sample(subscription_benefits, min(3, len(subscription_benefits)))
                benefits.extend(selected)
            
            # 케어서비스 포함 여부
            care_service = product.get('care_service', {})
            if care_service:
                service_types = care_service.get('service_types', [])
                if service_types:
                    benefits.append(f"전문 케어서비스 포함: {', '.join(service_types)}")
        
        return benefits
    
    def get_competitive_argument(self, product_id: int, stance: str, turn: int) -> str:
        """턴에 따른 경쟁적 논거 생성"""
        product = self.get_product_by_id(product_id)
        if not product:
            return ""
        
        arguments = {
            "구매": [
                # 턴 1: 가격 비교
                lambda p: f"{p['name']} 구매 시 {p.get('purchase_price', 0):,}원이면 끝! 구독은 6년 동안 총 {self.calculate_subscription_total(p):,}원 넘게 나가는데?",
                # 턴 2: 중고 판매 강조
                lambda p: f"구매하면 나중에 중고로 팔 수 있어! 최소 {int(p.get('purchase_price', 0) * 0.5):,}원은 회수 가능하지만 구독은 그냥 돈만 버리는 거야",
                # 턴 3: 위약금 공격
                lambda p: f"구독은 중간에 해지하면 위약금 폭탄! 잔여기간 요금의 최대 30%를 물어야 해",
                # 턴 4: 소유권 강조
                lambda p: f"내 것이 되는 게 최고야! 구독은 계속 남의 것, 구매는 영원히 내 것",
                # 턴 5: 월 고정비 부담
                lambda p: f"매달 {self.get_avg_subscription_price(p):,}원씩 나가는 구독료, 다른 데 쓰면 더 좋지 않아?"
            ],
            "구독": [
                # 턴 1: 초기 비용 부담
                lambda p: f"{p['name']} 구매하려면 한 번에 {p.get('purchase_price', 0):,}원! 이 돈으로 다른 것도 할 수 있는데?",
                # 턴 2: 케어서비스 강조
                lambda p: f"구독은 전문 케어서비스 포함! 구매는 AS 기간 지나면 수리비 폭탄",
                # 턴 3: 최신 제품 교체
                lambda p: f"6년 후 신제품으로 자연스럽게 교체! 구매한 제품은 6년 후면 구식이 돼",
                # 턴 4: 할인 혜택 강조
                lambda p: f"제휴카드로 월 최대 22,000원 할인! 멤버십 포인트도 쌓여서 실제론 훨씬 저렴해",
                # 턴 5: 고장 리스크
                lambda p: f"비싼 가전 구매 후 고장나면? 수리비 수십만원! 구독은 무상 AS로 걱정 끝"
            ]
        }
        
        stance_arguments = arguments.get(stance, [])
        if stance_arguments and turn <= len(stance_arguments):
            try:
                return stance_arguments[turn - 1](product)
            except:
                return ""
        return ""
    
    def calculate_subscription_total(self, product: Dict) -> int:
        """6년 구독 총 비용 계산"""
        subscription_prices = product.get('subscription_price', {})
        if '6년' in subscription_prices:
            return subscription_prices['6년'] * 72  # 6년 = 72개월
        elif subscription_prices:
            # 가장 긴 기간 선택
            longest = max(subscription_prices.keys(), key=lambda x: int(x.replace('년', '')))
            months = int(longest.replace('년', '')) * 12
            return subscription_prices[longest] * months
        return 0
    
    def get_avg_subscription_price(self, product: Dict) -> int:
        """평균 구독료 계산"""
        subscription_prices = product.get('subscription_price', {})
        if subscription_prices:
            return sum(subscription_prices.values()) // len(subscription_prices)
        return 0
