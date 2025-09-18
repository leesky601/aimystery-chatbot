import uvicorn
from config import Config

if __name__ == "__main__":
    # 환경변수 검증
    try:
        Config.validate()
        print("🚀 챗봇 대화 시스템을 시작합니다...")
        print(f"📍 서버 주소: http://{Config.HOST}:{Config.PORT}")
        print(f"📚 API 문서: http://{Config.HOST}:{Config.PORT}/docs")
        print("=" * 50)
        
        # 서버 실행 - v3 complete 사용
        uvicorn.run(
            "api_v3_complete:app",
            host=Config.HOST,
            port=Config.PORT,
            reload=True,
            log_level="info"
        )
        
    except ValueError as e:
        print(f"❌ 설정 오류: {e}")
        print("\n📝 .env 파일을 생성하고 다음 환경변수를 설정해주세요:")
        print("AZURE_OPENAI_API_KEY=your_api_key")
        print("AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        print("AZURE_OPENAI_API_VERSION=2024-02-15-preview")
        exit(1)
    except KeyboardInterrupt:
        print("\n👋 서버를 종료합니다.")
    except Exception as e:
        print(f"❌ 서버 실행 중 오류 발생: {e}")
        exit(1)
