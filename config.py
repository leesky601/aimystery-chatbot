import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 모델 선택 설정
    AI_PROVIDER = os.getenv("AI_PROVIDER", "azure")  # "azure" 또는 "exaone"
    
    # Azure AI Foundry 설정
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    
    # EXAONE 설정
    FRIENDLI_TOKEN = os.getenv("FRIENDLI_TOKEN")
    FRIENDLI_BASE_URL = os.getenv("FRIENDLI_BASE_URL", "https://api.friendli.ai/serverless/v1")
    EXAONE_MODEL = os.getenv("EXAONE_MODEL", "LGAI-EXAONE/EXAONE-4.0.1-32B")
    
    # 챗봇 모델 설정
    CHATBOT_1_MODEL = os.getenv("CHATBOT_1_MODEL", "gpt-4o")
    CHATBOT_2_MODEL = os.getenv("CHATBOT_2_MODEL", "gpt-4o")
    CHATBOT_3_MODEL = os.getenv("CHATBOT_3_MODEL", "gpt-4o")
    
    # 네이버 클로바 TTS 설정
    NAVER_CLOVA_CLIENT_ID = os.getenv("NAVER_CLOVA_CLIENT_ID")
    NAVER_CLOVA_CLIENT_SECRET = os.getenv("NAVER_CLOVA_CLIENT_SECRET")
    
    # 웹서버 설정
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8080))
    
    @classmethod
    def validate(cls):
        """필수 환경변수 검증"""
        if cls.AI_PROVIDER == "azure":
            required_vars = [
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_DEPLOYMENT_NAME"
            ]
        elif cls.AI_PROVIDER == "exaone":
            required_vars = [
                "FRIENDLI_TOKEN"
            ]
        else:
            raise ValueError(f"지원하지 않는 AI_PROVIDER입니다: {cls.AI_PROVIDER}. 'azure' 또는 'exaone'을 사용하세요.")
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        
        return True
