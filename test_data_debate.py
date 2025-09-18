#!/usr/bin/env python3
"""
데이터 기반 논쟁 테스트 스크립트
"""

import asyncio
from product_manager import ProductManager
from chatbots import ChatBotManager

async def test_data_driven_debate():
    """데이터 기반 논쟁 테스트"""
    
    # 매니저 초기화
    chatbot_manager = ChatBotManager()
    product_manager = ProductManager()
    
    # 모든 제품 정보 출력
    print("=" * 60)
    print("사용 가능한 제품 목록:")
    print("=" * 60)
    products = product_manager.get_all_products()
    for product in products:
        print(f"ID: {product['id']}, 이름: {product['name']}")
        print(f"  구매가격: {product.get('purchase_price', 0):,}원")
        if product.get('subscription_price'):
            print("  구독가격:")
            for period, price in product['subscription_price'].items():
                print(f"    - {period}: 월 {price:,}원")
        print("-" * 40)
    
    # 테스트할 제품 ID (LG 퓨리케어 오브제컬렉션 정수기)
    test_product_id = 1
    
    print("\n" + "=" * 60)
    print(f"제품 ID {test_product_id}에 대한 데이터 기반 논쟁 시작")
    print("=" * 60)
    
    # 논쟁 실행
    try:
        result = await chatbot_manager.start_debate_with_product(
            product_id=test_product_id,
            max_turns=3,  # 3턴으로 테스트
            user_info="30대 직장인, 월 예산 5만원 정도 생각중"
        )
        
        # 결과 출력
        print("\n📝 논쟁 결과:")
        print("=" * 60)
        for idx, turn in enumerate(result, 1):
            speaker = turn.get('speaker', '알 수 없음')
            message = turn.get('message', '')
            
            # 스피커별 이모지
            emoji = "🤖"
            if speaker == "구매봇":
                emoji = "💰"
            elif speaker == "구독봇":
                emoji = "📅"
            elif speaker == "안내봇":
                emoji = "📢"
            
            print(f"\n{emoji} [{speaker}] (턴 {idx})")
            print("-" * 40)
            print(message)
        
        print("\n" + "=" * 60)
        print("✅ 데이터 기반 논쟁 테스트 완료!")
        print("=" * 60)
        
        # 데이터 사용 통계
        print("\n📊 데이터 사용 분석:")
        print("=" * 60)
        
        for turn in result:
            speaker = turn.get('speaker', '')
            message = turn.get('message', '')
            
            if speaker in ['구매봇', '구독봇']:
                # 숫자(가격) 언급 확인
                import re
                numbers = re.findall(r'\d{1,3}(?:,\d{3})*원', message)
                if numbers:
                    print(f"{speaker}: 구체적인 가격 데이터 {len(numbers)}개 사용")
                    for num in numbers:
                        print(f"  - {num}")
                
                # 특정 키워드 확인
                keywords = ['케어서비스', '멤버십', '위약금', '할인', 'AS', '중고', '포인트']
                used_keywords = [kw for kw in keywords if kw in message]
                if used_keywords:
                    print(f"{speaker}: 제품 특징 키워드 사용: {', '.join(used_keywords)}")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🚀 데이터 기반 논쟁 테스트 시작...\n")
    asyncio.run(test_data_driven_debate())