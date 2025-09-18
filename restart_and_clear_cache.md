# 🔧 문제 해결 가이드

## 문제 진단

현재 상황:
1. ✅ 백엔드 코드는 정상 (데이터 기반 응답 생성 확인)
2. ✅ API는 정상적으로 응답 전송 (콘솔 로그에서 확인)
3. ❌ 프론트엔드에서 메시지가 화면에 표시되지 않음
4. ⚠️ FRIENDLI_TOKEN이 설정되지 않아 EXAONE API 호출 실패 가능성

## 해결 방법

### 1. 서버 재시작 (필수)

```bash
# 기존 서버 중지 (Ctrl+C)

# 서버 재시작
cd /home/user/webapp
python main.py
```

### 2. 브라우저 캐시 완전 삭제

#### Chrome/Edge:
1. **F12** 키를 눌러 개발자 도구 열기
2. **Network** 탭 선택
3. **Disable cache** 체크박스 선택
4. **Ctrl + Shift + R** (강력 새로고침)

또는

1. **Ctrl + Shift + Delete**
2. 캐시된 이미지 및 파일 선택
3. 삭제

#### 직접 URL로 접근:
```
http://localhost:8080/static/index.html?v=2
```
(쿼리 파라미터 추가로 캐시 무시)

### 3. EXAONE API 설정 (선택사항)

실제 EXAONE API를 사용하려면:

1. `.env` 파일 수정:
```env
AI_PROVIDER=exaone
FRIENDLI_TOKEN=your_actual_friendli_token_here  # 실제 토큰 입력
FRIENDLI_BASE_URL=https://api.friendli.ai/serverless/v1
```

2. Friendli 토큰 얻기:
   - https://suite.friendli.ai 에서 회원가입
   - API Keys 메뉴에서 토큰 생성

### 4. Azure 모드로 전환 (대안)

EXAONE 토큰이 없다면 Azure 모드로 전환:

`.env` 파일:
```env
AI_PROVIDER=azure
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

### 5. 테스트용 로컬 모드

API 없이 데이터만으로 테스트:
```bash
python test_local_debate.py 0  # TV 제품 테스트
python test_local_debate.py 1  # 정수기 테스트
python test_local_debate.py all  # 모든 제품 테스트
```

## 확인 사항

### 콘솔에서 확인할 내용:
```javascript
// 브라우저 콘솔에서 실행
console.log('Checking streaming data...');

// 네트워크 탭에서 확인:
// 1. /product/debate/stream 요청이 있는지
// 2. Response 탭에서 data: {type: 'streaming', content: '...'} 형태인지
// 3. content 필드가 있는지 (chunk가 아닌)
```

### 코드 확인:
현재 수정된 코드:
- ✅ `data.chunk` → `data.content`로 변경됨
- ✅ API에서 `content` 필드로 전송
- ✅ 프론트엔드에서 `data.content` 읽기

## 디버깅 팁

1. **네트워크 탭 확인**:
   - EventStream 응답 확인
   - data 형식 확인

2. **콘솔 로그 확인**:
   - `Invalid or empty chunk: undefined` → 캐시 문제
   - `Streaming chunk from: 구매봇 content: ...` → 정상

3. **강제 리로드**:
   - Shift + F5
   - Ctrl + Shift + R
   - 시크릿 모드에서 테스트

## 최종 체크리스트

- [ ] 서버 재시작했는가?
- [ ] 브라우저 캐시 삭제했는가?
- [ ] .env 파일에 올바른 토큰이 있는가?
- [ ] 콘솔에서 `content` 필드를 읽고 있는가?
- [ ] 네트워크 탭에서 스트리밍 데이터가 오는가?

## 문제가 계속되면

1. 시크릿/프라이빗 브라우징 모드로 테스트
2. 다른 브라우저로 테스트
3. `index.html?v=timestamp` 형태로 접근
4. 서버 로그 확인 (`python main.py` 실행 창)