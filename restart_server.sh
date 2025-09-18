#!/bin/bash

echo "🚀 서버와 ngrok을 중지하고 재시작합니다..."

# 기존 프로세스들 종료
echo "기존 프로세스들을 찾는 중..."

# 포트 8080에서 실행 중인 서버 프로세스 종료
SERVER_PID=$(lsof -ti:8080)
if [ ! -z "$SERVER_PID" ]; then
    echo "포트 8080에서 실행 중인 서버 프로세스 (PID: $SERVER_PID)를 종료합니다..."
    kill -9 $SERVER_PID
    sleep 1
fi

# ngrok 프로세스 종료
NGROK_PID=$(pgrep -f "ngrok")
if [ ! -z "$NGROK_PID" ]; then
    echo "ngrok 프로세스 (PID: $NGROK_PID)를 종료합니다..."
    kill -9 $NGROK_PID
    sleep 1
fi

echo "기존 프로세스들이 종료되었습니다."

# 가상환경 활성화 및 서버 시작 (백그라운드)
echo "가상환경을 활성화하고 서버를 시작합니다..."
source venv/bin/activate
python main.py &
SERVER_PID=$!

# 서버 시작 대기
echo "서버 시작을 기다리는 중..."
sleep 3

# ngrok 시작 (백그라운드) - 고정 URL 사용
echo "ngrok 터널을 시작합니다 (고정 URL: unexpeditious-tricia-unblenchingly.ngrok-free.app)..."
./ngrok http --url=unexpeditious-tricia-unblenchingly.ngrok-free.app 8080 &
NGROK_PID=$!

# ngrok 시작 대기
echo "ngrok 시작을 기다리는 중..."
sleep 3

# 터널 정보 가져오기
echo "🌐 터널 정보를 가져오는 중..."
sleep 2

# 터널 URL 출력
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['tunnels'][0]['public_url']) if data.get('tunnels') else print('터널을 찾을 수 없습니다')" 2>/dev/null)

if [ ! -z "$PUBLIC_URL" ] && [ "$PUBLIC_URL" != "터널을 찾을 수 없습니다" ]; then
    echo ""
    echo "✅ 서버와 ngrok이 성공적으로 시작되었습니다!"
    echo "📍 로컬 서버: http://localhost:8080"
    echo "🌐 공개 URL: $PUBLIC_URL"
    echo "📱 웹 인터페이스: $PUBLIC_URL/static/index.html"
    echo ""
    echo "🛑 종료하려면 Ctrl+C를 누르세요"
    echo ""
else
    echo "⚠️  ngrok 터널 정보를 가져올 수 없습니다. 수동으로 확인해주세요."
    echo "📍 로컬 서버: http://localhost:8080"
    echo "🌐 ngrok 웹 인터페이스: http://localhost:4040"
fi

# 프로세스들이 종료될 때까지 대기
wait
