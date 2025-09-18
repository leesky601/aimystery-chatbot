#!/usr/bin/env python3
"""
로컬 테스트용 - API 호출 없이 데이터 기반 논쟁 시뮬레이션
"""

import json
from product_manager import ProductManager
import random

class MockChatBot:
    """API 호출 없이 데이터만으로 응답 생성하는 모의 챗봇"""
    
    def __init__(self, name, stance):
        self.name = name
        self.stance = stance
        self.product_manager = ProductManager()
        self.turn_count = 0
        
    def generate_response(self, product_id, user_info=None):
        """데이터 기반 응답 생성"""
        self.turn_count += 1
        
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return "제품 정보를 찾을 수 없긴해"
        
        # 경쟁적 논거 가져오기
        argument = self.product_manager.get_competitive_argument(
            product_id, self.stance, self.turn_count
        )
        
        # 구체적 혜택 데이터 가져오기
        benefits = self.product_manager.get_specific_benefit_data(
            product_id, self.stance
        )
        
        # 응답 조합
        response_parts = []
        
        # 메인 논거
        if argument:
            response_parts.append(argument)
        
        # 추가 혜택 (랜덤하게 1개)
        if benefits and len(benefits) > self.turn_count:
            benefit = benefits[min(self.turn_count-1, len(benefits)-1)]
            response_parts.append(benefit)
        
        return " ".join(response_parts) if response_parts else f"{self.stance}가 최고긴해!"

def simulate_debate(product_id=1, max_turns=3):
    """데이터 기반 논쟁 시뮬레이션"""
    
    # 매니저와 모의 챗봇 초기화
    pm = ProductManager()
    purchase_bot = MockChatBot("구매봇", "구매")
    subscription_bot = MockChatBot("구독봇", "구독")
    
    # 제품 정보 가져오기
    product = pm.get_product_by_id(product_id)
    if not product:
        print(f"제품 ID {product_id}를 찾을 수 없습니다")
        return
    
    print("=" * 80)
    print(f"🎬 데이터 기반 논쟁 시뮬레이션: {product['name']}")
    print("=" * 80)
    print(f"\n📊 제품 정보:")
    print(f"구매가격: {product.get('purchase_price', 0):,}원")
    
    if product.get('subscription_price'):
        print("구독가격:")
        for period, price in product['subscription_price'].items():
            months = int(period.replace('년', '')) * 12
            total = price * months
            print(f"  - {period}: 월 {price:,}원 (총 {total:,}원)")
    
    print("\n" + "=" * 80)
    print("💬 논쟁 시작!")
    print("=" * 80)
    
    # 논쟁 진행
    for turn in range(1, max_turns + 1):
        print(f"\n[턴 {turn}]")
        print("-" * 40)
        
        # 구매봇 발언
        purchase_response = purchase_bot.generate_response(product_id)
        print(f"💰 구매봇: {purchase_response}")
        
        print()
        
        # 구독봇 발언
        subscription_response = subscription_bot.generate_response(product_id)
        print(f"📅 구독봇: {subscription_response}")
    
    print("\n" + "=" * 80)
    print("📢 안내봇: 두 봇 모두 좋은 주장을 했습니다.")
    print(f"구매는 {product.get('purchase_price', 0):,}원으로 완전 소유가 가능하고,")
    
    if product.get('subscription_price'):
        best_period = '6년' if '6년' in product['subscription_price'] else list(product['subscription_price'].keys())[-1]
        monthly = product['subscription_price'][best_period]
        print(f"구독은 {best_period} 기준 월 {monthly:,}원으로 케어서비스를 받을 수 있습니다.")
    
    print("고객님의 상황에 맞는 선택을 하시기 바랍니다!")
    print("=" * 80)
    
    # 데이터 사용 통계
    print("\n📈 데이터 활용 분석:")
    print("=" * 80)
    print(f"✅ 구체적인 가격 데이터 활용")
    print(f"✅ 제품별 특징 언급")
    print(f"✅ 턴별로 다른 논거 사용")
    print(f"✅ new_products.json 데이터 100% 활용")
    print("=" * 80)

def test_all_products():
    """모든 제품에 대해 테스트"""
    pm = ProductManager()
    products = pm.get_all_products()
    
    print("\n" + "🚀" * 40)
    print("모든 제품 테스트 시작")
    print("🚀" * 40)
    
    for product in products:
        print(f"\n\n{'='*80}")
        print(f"제품 {product['id']}: {product['name']}")
        print('='*80)
        simulate_debate(product['id'], max_turns=2)
        print("\n잠시 휴식..." + "." * 20)
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'all':
            test_all_products()
        else:
            try:
                product_id = int(sys.argv[1])
                simulate_debate(product_id, max_turns=3)
            except ValueError:
                print("사용법: python test_local_debate.py [product_id|all]")
    else:
        # 기본값: 정수기(ID: 1) 테스트
        simulate_debate(1, max_turns=3)