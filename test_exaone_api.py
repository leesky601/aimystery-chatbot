#!/usr/bin/env python3
"""
EXAONE API 연결 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일 로드
load_dotenv()

def test_exaone_connection():
    """EXAONE API 연결 테스트"""
    
    print("=" * 60)
    print("🔍 EXAONE API 설정 확인")
    print("=" * 60)
    
    # 환경 변수 확인
    ai_provider = os.getenv("AI_PROVIDER")
    token = os.getenv("FRIENDLI_TOKEN")
    base_url = os.getenv("FRIENDLI_BASE_URL")
    model = os.getenv("EXAONE_MODEL", "LGAI-EXAONE/EXAONE-4.0.1-32B")
    
    print(f"AI_PROVIDER: {ai_provider}")
    print(f"FRIENDLI_TOKEN: {'설정됨' if token else '❌ 미설정'}")
    print(f"FRIENDLI_BASE_URL: {base_url}")
    print(f"EXAONE_MODEL: {model}")
    
    if ai_provider != "exaone":
        print(f"\n⚠️ AI_PROVIDER가 '{ai_provider}'로 설정되어 있습니다.")
        print("EXAONE을 사용하려면 AI_PROVIDER=exaone으로 설정하세요.")
        return False
    
    if not token:
        print("\n❌ FRIENDLI_TOKEN이 설정되지 않았습니다!")
        print("실제 토큰을 .env 파일에 추가해주세요.")
        return False
    
    # API 테스트
    print("\n" + "=" * 60)
    print("📡 EXAONE API 호출 테스트")
    print("=" * 60)
    
    try:
        client = OpenAI(
            api_key=token,
            base_url=base_url,
        )
        
        # 간단한 테스트 메시지
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다."},
                {"role": "user", "content": "안녕하세요? 간단히 인사해주세요."}
            ],
            max_tokens=50,
            temperature=0.7,
            stream=False
        )
        
        if response and response.choices:
            print("✅ API 호출 성공!")
            print(f"응답: {response.choices[0].message.content}")
            return True
        else:
            print("❌ API 응답이 비어있습니다.")
            return False
            
    except Exception as e:
        print(f"❌ API 호출 실패!")
        print(f"오류: {str(e)}")
        
        # 일반적인 오류 원인 안내
        if "401" in str(e) or "Unauthorized" in str(e):
            print("\n💡 해결 방법:")
            print("1. FRIENDLI_TOKEN이 올바른지 확인하세요")
            print("2. https://suite.friendli.ai 에서 토큰을 재발급 받으세요")
        elif "404" in str(e):
            print("\n💡 해결 방법:")
            print("1. EXAONE_MODEL 이름이 올바른지 확인하세요")
            print("2. 기본값: LGAI-EXAONE/EXAONE-4.0.1-32B")
        elif "Connection" in str(e) or "Network" in str(e):
            print("\n💡 해결 방법:")
            print("1. 인터넷 연결을 확인하세요")
            print("2. FRIENDLI_BASE_URL이 올바른지 확인하세요")
            print("3. 기본값: https://api.friendli.ai/serverless/v1")
        
        return False

def test_chat_response():
    """데이터 기반 응답 생성 테스트"""
    
    print("\n" + "=" * 60)
    print("💬 데이터 기반 응답 생성 테스트")
    print("=" * 60)
    
    token = os.getenv("FRIENDLI_TOKEN")
    base_url = os.getenv("FRIENDLI_BASE_URL")
    model = os.getenv("EXAONE_MODEL", "LGAI-EXAONE/EXAONE-4.0.1-32B")
    
    if not token:
        print("❌ FRIENDLI_TOKEN이 설정되지 않아 테스트할 수 없습니다.")
        return
    
    try:
        client = OpenAI(
            api_key=token,
            base_url=base_url,
        )
        
        # 구매봇 테스트
        purchase_prompt = """당신은 구매봇입니다.
        LG 정수기 구매를 추천하세요.
        구매가격: 1,128,000원
        구독가격: 6년 월 28,900원 (총 2,080,800원)
        
        구체적인 가격을 언급하며 구매가 왜 좋은지 설명하세요."""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "킹받는 급식체로 말하세요. 문장 끝은 '~긴해'로 끝내세요."},
                {"role": "user", "content": purchase_prompt}
            ],
            max_tokens=150,
            temperature=0.7,
            stream=False
        )
        
        if response and response.choices:
            print("🤖 구매봇 응답:")
            print(response.choices[0].message.content)
            print("\n✅ 데이터 기반 응답 생성 성공!")
        
    except Exception as e:
        print(f"❌ 응답 생성 실패: {str(e)}")

if __name__ == "__main__":
    print("\n🚀 EXAONE API 테스트 시작...\n")
    
    # 연결 테스트
    if test_exaone_connection():
        # 응답 생성 테스트
        test_chat_response()
    else:
        print("\n⚠️ API 연결에 실패했습니다. 위의 안내를 참고하세요.")
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)