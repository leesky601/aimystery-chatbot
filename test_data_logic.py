#!/usr/bin/env python3
"""
데이터 기반 논리 테스트 (API 호출 없이)
"""

import json
from product_manager import ProductManager

def test_product_manager():
    """ProductManager의 데이터 분석 메서드 테스트"""
    
    # 매니저 초기화
    pm = ProductManager()
    
    # 모든 제품 정보 출력
    print("=" * 60)
    print("📦 제품 데이터 로드 테스트")
    print("=" * 60)
    
    products = pm.get_all_products()
    print(f"✅ 총 {len(products)}개 제품 로드됨")
    
    for product in products:
        print(f"\n제품 ID: {product['id']}")
        print(f"제품명: {product['name']}")
        print(f"구매가격: {product.get('purchase_price', 0):,}원")
        
        if product.get('subscription_price'):
            print("구독가격:")
            for period, price in product['subscription_price'].items():
                print(f"  - {period}: 월 {price:,}원")
    
    print("\n" + "=" * 60)
    print("🔍 데이터 분석 메서드 테스트")
    print("=" * 60)
    
    # 테스트할 제품 ID (정수기)
    test_product_id = 1
    product = pm.get_product_by_id(test_product_id)
    
    if product:
        print(f"\n테스트 제품: {product['name']}")
        print("-" * 40)
        
        # 1. 총 비용 계산 테스트
        print("\n💰 총 비용 계산:")
        for period in product.get('subscription_price', {}).keys():
            sub_cost, sub_detail = pm.calculate_total_cost(test_product_id, period, True)
            print(f"  구독 {period}: {sub_detail}")
        
        purchase_cost, purchase_detail = pm.calculate_total_cost(test_product_id, "6년", False)
        print(f"  구매: {purchase_detail}")
        
        # 2. 구체적인 혜택 데이터 추출
        print("\n📋 구매 혜택 데이터:")
        purchase_benefits = pm.get_specific_benefit_data(test_product_id, "구매")
        for idx, benefit in enumerate(purchase_benefits, 1):
            print(f"  {idx}. {benefit}")
        
        print("\n📋 구독 혜택 데이터:")
        subscription_benefits = pm.get_specific_benefit_data(test_product_id, "구독")
        for idx, benefit in enumerate(subscription_benefits, 1):
            print(f"  {idx}. {benefit}")
        
        # 3. 경쟁적 논거 생성
        print("\n⚔️ 경쟁적 논거 (각 턴별):")
        print("\n[구매봇 논거]")
        for turn in range(1, 4):
            argument = pm.get_competitive_argument(test_product_id, "구매", turn)
            if argument:
                print(f"  턴 {turn}: {argument}")
        
        print("\n[구독봇 논거]")
        for turn in range(1, 4):
            argument = pm.get_competitive_argument(test_product_id, "구독", turn)
            if argument:
                print(f"  턴 {turn}: {argument}")
        
        # 4. 위약금 정보
        print("\n⚠️ 위약금 정보:")
        penalty_info = pm.get_penalty_info()
        if penalty_info:
            early_termination = penalty_info.get('early_termination_fee', {})
            if early_termination:
                print(f"  설명: {early_termination.get('description', '')}")
                rates = early_termination.get('rates', {})
                for period, rate in rates.items():
                    print(f"  - {period}: {rate}")
        
        # 5. 공통 혜택
        print("\n🎁 공통 혜택:")
        print("\n[구매 공통 혜택]")
        common_purchase = pm.get_common_purchase_benefits()
        for idx, benefit in enumerate(common_purchase[:3], 1):  # 처음 3개만
            print(f"  {idx}. {benefit}")
        
        print("\n[구독 공통 혜택]")
        common_subscription = pm.get_common_subscription_benefits()
        for idx, benefit in enumerate(common_subscription[:3], 1):  # 처음 3개만
            print(f"  {idx}. {benefit}")
    
    print("\n" + "=" * 60)
    print("✅ 데이터 논리 테스트 완료!")
    print("=" * 60)
    
    # 데이터 기반 대화 시뮬레이션
    print("\n" + "=" * 60)
    print("💬 데이터 기반 대화 시뮬레이션")
    print("=" * 60)
    
    print("\n시나리오: LG 정수기 구매 vs 구독 논쟁")
    print("-" * 40)
    
    # 턴 1
    print("\n[턴 1]")
    purchase_arg = pm.get_competitive_argument(test_product_id, "구매", 1)
    print(f"구매봇: {purchase_arg}")
    
    subscription_arg = pm.get_competitive_argument(test_product_id, "구독", 1)
    print(f"구독봇: {subscription_arg}")
    
    # 턴 2
    print("\n[턴 2]")
    purchase_arg = pm.get_competitive_argument(test_product_id, "구매", 2)
    print(f"구매봇: {purchase_arg}")
    
    subscription_arg = pm.get_competitive_argument(test_product_id, "구독", 2)
    print(f"구독봇: {subscription_arg}")
    
    # 턴 3
    print("\n[턴 3]")
    purchase_arg = pm.get_competitive_argument(test_product_id, "구매", 3)
    print(f"구매봇: {purchase_arg}")
    
    subscription_arg = pm.get_competitive_argument(test_product_id, "구독", 3)
    print(f"구독봇: {subscription_arg}")
    
    print("\n" + "=" * 60)
    print("🎯 시뮬레이션 완료! 데이터 기반 논거가 잘 작동합니다.")
    print("=" * 60)

if __name__ == "__main__":
    print("\n🚀 데이터 기반 논리 테스트 시작...\n")
    test_product_manager()