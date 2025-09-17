@echo off
REM ========================================
REM   YouTube Summarizer 서버 시작
REM   OAuth2 인증 모드
REM ========================================

echo ========================================
echo   YouTube Summarizer 서버 시작
echo   OAuth2 인증 모드
echo ========================================
echo.

REM 스크립트 디렉토리에서 프로젝트 루트로 이동
cd /d "%~dp0\.."

REM Chrome 상태 확인
echo [1/4] Chrome 브라우저 상태 확인 중...
tasklist /FI "IMAGENAME eq chrome.exe" 2>nul | find /I /N "chrome.exe">nul
if "%ERRORLEVEL%"=="0" (
    echo.
    echo ╔═══════════════════════════════════════════════════════════╗
    echo ║           ⚠️  Chrome이 실행 중입니다!                      ║
    echo ╠═══════════════════════════════════════════════════════════╣
    echo ║  멤버십 영상 접근을 위해서는:                             ║
    echo ║                                                            ║
    echo ║  옵션 1: Chrome을 완전히 종료하세요                       ║
    echo ║  옵션 2: Chrome 바로가기에 다음 플래그 추가:              ║
    echo ║          --disable-features=LockProfileCookieDatabase     ║
    echo ║  옵션 3: cookies.txt 파일 사용 (있는 경우)                ║
    echo ║                                                            ║
    echo ║  일반 영상은 그대로 처리 가능합니다.                      ║
    echo ╚═══════════════════════════════════════════════════════════╝
    echo.
    echo 계속하시겠습니까? (Y/N)
    choice /C YN /N
    if errorlevel 2 (
        echo Chrome을 종료한 후 다시 실행하세요.
        pause
        exit /b 1
    )
)

REM Git 최신 변경사항 가져오기
echo.
echo [2/4] GitHub에서 최신 코드 가져오는 중...
git pull origin main
if errorlevel 1 (
    echo [WARNING] Git pull 실패. 로컬 버전으로 계속합니다.
)

REM 가상환경 확인 및 활성화
echo.
echo [3/4] Python 가상환경 확인 중...
if exist venv\Scripts\activate.bat (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate
) else (
    echo [WARNING] 가상환경이 없습니다. 생성하시겠습니까? (Y/N)
    choice /C YN /N
    if errorlevel 1 (
        echo 가상환경 생성 중...
        python -m venv venv
        call venv\Scripts\activate
        echo 패키지 설치 중...
        pip install -r requirements.txt
    )
)

REM Tailscale IP 확인
echo.
echo [4/4] Tailscale 상태 확인 중...
if exist "C:\Program Files\Tailscale\tailscale.exe" (
    "C:\Program Files\Tailscale\tailscale.exe" ip -4 >nul 2>&1
    if not errorlevel 1 (
        echo ✅ Tailscale 연결됨
        for /f "tokens=*" %%i in ('"C:\Program Files\Tailscale\tailscale.exe" ip -4') do set TAILSCALE_IP=%%i
        echo    IP 주소: %TAILSCALE_IP%
    ) else (
        echo ⚠️  Tailscale이 실행 중이지 않습니다
        echo    로컬 접속만 가능합니다 (http://localhost:8000)
    )
) else (
    echo ⚠️  Tailscale이 설치되지 않았습니다
    echo    로컬 접속만 가능합니다 (http://localhost:8000)
)

echo.
echo ========================================
echo   서버를 시작합니다...
echo ========================================
echo.
echo 접속 주소:
echo   - 로컬: http://localhost:8000
if defined TAILSCALE_IP (
    echo   - Tailscale: http://%TAILSCALE_IP%:8000
)
echo   - API 문서: http://localhost:8000/docs
echo   - 쿠키 상태: http://localhost:8000/api/auth/cookie/status
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

REM 서버 실행 (모든 인터페이스에서 접근 가능)
if exist run.py (
    python run.py --host 0.0.0.0 --port 8000
) else (
    REM run.py가 없으면 직접 uvicorn 실행
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)

pause