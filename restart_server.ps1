# PowerShell 스크립트로 서버 재시작
# 인코딩 설정 - 한글 출력 문제 해결
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 콘솔 코드페이지를 UTF-8로 설정
chcp 65001 > $null

Write-Host "Server restart script starting..." -ForegroundColor Green

# 기존 프로세스들 종료
Write-Host "Finding existing processes..." -ForegroundColor Yellow

# 포트 8080에서 실행 중인 서버 프로세스 종료
try {
    $serverProcess = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
    if ($serverProcess) {
        Write-Host "Stopping server process on port 8080 (PID: $serverProcess)..." -ForegroundColor Yellow
        Stop-Process -Id $serverProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Host "Error checking port 8080 process: $_" -ForegroundColor Red
}

Write-Host "Existing processes terminated." -ForegroundColor Green

# 가상환경 활성화 및 서버 시작
Write-Host "Activating virtual environment and starting server..." -ForegroundColor Green

# 가상환경 확인 및 활성화 (Windows)
$venvActivated = $false
if (Test-Path "venv\Scripts\Activate.ps1") {
    try {
        & "venv\Scripts\Activate.ps1"
        $venvActivated = $true
        Write-Host "Virtual environment activated." -ForegroundColor Green
    } catch {
        Write-Host "Failed to activate virtual environment: $_" -ForegroundColor Red
    }
} elseif (Test-Path "venv\Scripts\activate.bat") {
    try {
        cmd /c "venv\Scripts\activate.bat"
        $venvActivated = $true
        Write-Host "Virtual environment activated." -ForegroundColor Green
    } catch {
        Write-Host "Failed to activate virtual environment: $_" -ForegroundColor Red
    }
}

if (-not $venvActivated) {
    Write-Host "Virtual environment not found. Using global Python." -ForegroundColor Yellow
}

# Python 실행 파일 찾기 (Windows에서는 python 우선)
$pythonCmd = "python"
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    if (Get-Command "python3" -ErrorAction SilentlyContinue) {
        $pythonCmd = "python3"
    } elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
        $pythonCmd = "py"
    } else {
        Write-Host "Python not found!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Python command: $pythonCmd" -ForegroundColor Cyan
Write-Host "Starting Python server..." -ForegroundColor Green

# 서버 상태 확인 및 출력
Write-Host ""
Write-Host "Server starting..." -ForegroundColor Green
Write-Host "Local server: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Web interface: http://localhost:8080/static/index.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Ctrl+C 핸들러 등록
$null = Register-EngineEvent PowerShell.Exiting -Action {
    Write-Host "Script terminating..." -ForegroundColor Yellow
    
    # 프로세스 정리
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*main.py*" } | Stop-Process -Force -ErrorAction SilentlyContinue
}

# 서버 직접 실행 (Job 사용하지 않음)
try {
    & $pythonCmd main.py
} catch {
    Write-Host "Server execution failed: $_" -ForegroundColor Red
} finally {
    Write-Host "Server stopped." -ForegroundColor Yellow
}