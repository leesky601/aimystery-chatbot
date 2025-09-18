# 챗봇 대화 시스템

Azure AI Foundry를 사용하여 두 개의 AI 챗봇이 주제에 대해 대화하는 FastAPI 웹서버입니다.

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Azure AI Foundry 설정
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# 챗봇 모델 설정 (선택사항)
CHATBOT_1_MODEL=gpt-4o
CHATBOT_2_MODEL=gpt-4o
CHATBOT_3_MODEL=gpt-4o

# 네이버 클로바 TTS 설정 (선택사항 - 음성 기능용)
NAVER_CLOVA_CLIENT_ID=your_naver_clova_client_id
NAVER_CLOVA_CLIENT_SECRET=your_naver_clova_client_secret

# 웹서버 설정 (선택사항)
HOST=0.0.0.0
PORT=8000
```

### 3. 서버 실행

```bash
python main.py
```

서버가 실행되면 다음 주소에서 접근할 수 있습니다:
- API 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs

## 📡 API 엔드포인트

### 1. 챗봇 간 대화 시작
```http
POST /conversation/start
Content-Type: application/json

{
    "topic": "인공지능의 미래",
    "max_turns": 10
}
```

### 2. 개별 챗봇과 대화
```http
POST /chat/single
Content-Type: application/json

{
    "message": "안녕하세요!",
    "chatbot_name": "알파"
}
```

### 3. 대화 히스토리 조회
```http
GET /conversation/history
```

### 4. 대화 히스토리 초기화
```http
DELETE /conversation/clear
```

### 5. 헬스 체크
```http
GET /health
```

## 🤖 챗봇 특징

- **알파**: 호기심이 많고 질문을 많이 하는 탐구형 성격
- **베타**: 논리적이고 분석적인 사고를 하는 전문가형 성격

## 🛠️ 사용 예시

### Python 클라이언트 예시

```python
import requests

# 챗봇 간 대화 시작
response = requests.post("http://localhost:8000/conversation/start", 
                        json={"topic": "기후변화", "max_turns": 8})
conversation = response.json()

for turn in conversation["conversation"]:
    print(f"[{turn['speaker']}] {turn['message']}")
```

### cURL 예시

```bash
# 대화 시작
curl -X POST "http://localhost:8000/conversation/start" \
     -H "Content-Type: application/json" \
     -d '{"topic": "우주 탐험", "max_turns": 6}'

# 개별 챗봇과 대화
curl -X POST "http://localhost:8000/chat/single" \
     -H "Content-Type: application/json" \
     -d '{"message": "안녕하세요!", "chatbot_name": "베타"}'
```

## 🔧 설정

- `max_turns`: 최대 대화 턴 수 (1-20)
- `temperature`: AI 응답의 창의성 수준 (0.7로 설정)
- `max_tokens`: 최대 응답 길이 (500토큰)

## 🔊 음성 기능 (TTS)

이 시스템은 네이버 클로바 TTS를 사용하여 챗봇 메시지를 음성으로 재생합니다.

### 네이버 클로바 TTS 설정

1. [네이버 클라우드 플랫폼](https://www.ncloud.com/)에 가입
2. AI Service > Clova Speech > TTS 서비스 신청
3. API 키 발급 후 `.env` 파일에 추가:

```env
NAVER_CLOVA_CLIENT_ID=your_client_id
NAVER_CLOVA_CLIENT_SECRET=your_client_secret
```

### 음성 옵션

- **구매봇**: `jinho` (남성 음성)
- **구독봇**: `nara` (여성 음성)  
- **안내봇**: `nara` (여성 음성)

### 대안 음성

클로바 TTS가 설정되지 않은 경우 브라우저의 내장 Speech Synthesis API를 자동으로 사용합니다.

## 📝 주의사항

1. Azure AI Foundry에서 적절한 권한이 설정되어 있어야 합니다
2. API 키와 엔드포인트가 올바르게 설정되어야 합니다
3. 모델 배포가 완료되어 있어야 합니다
4. 음성 기능 사용 시 네이버 클로바 TTS API 키가 필요합니다 (선택사항)
