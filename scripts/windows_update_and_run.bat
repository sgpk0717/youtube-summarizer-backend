@echo off
echo ========================================
echo   YouTube Summarizer 업데이트 및 실행
echo   Windows 환경
echo ========================================
echo.

REM 프로젝트 디렉토리로 이동
cd /d C:\youtube-summarizer\backend

REM Git 최신 변경사항 가져오기
echo [1/5] GitHub에서 최신 코드 가져오는 중...
git pull origin main

REM 가상환경 활성화
echo [2/5] Python 가상환경 활성화...
call venv\Scripts\activate

REM 패키지 업데이트 (requirements.txt 변경시)
echo [3/5] Python 패키지 확인 및 업데이트...
pip install -r requirements.txt --quiet

REM Tailscale 상태 확인
echo [4/5] Tailscale 상태 확인...
"C:\Program Files\Tailscale\tailscale.exe" ip -4

REM 서버 시작
echo [5/5] 서버 시작...
echo.
echo ========================================
echo   서버가 실행 중입니다.
echo   Ctrl+C로 종료
echo ========================================
echo.

python run.py --host 0.0.0.0 --port 8000

pause