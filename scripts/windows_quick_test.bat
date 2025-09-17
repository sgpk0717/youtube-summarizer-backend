@echo off
echo ========================================
echo   빠른 업데이트 및 테스트
echo ========================================

cd /d C:\youtube-summarizer\backend

REM Git 상태 확인
echo [1/3] Git 상태 확인...
git status --short

REM 최신 변경사항 가져오기
echo [2/3] 최신 코드 가져오기...
git pull origin main

REM 변경된 파일 목록 표시
echo.
echo 변경된 파일:
git diff --name-only HEAD@{1}

echo.
echo [3/3] 서버 실행하려면 아무 키나 누르세요...
pause

REM 가상환경 활성화 및 실행
call venv\Scripts\activate
python run.py --host 0.0.0.0 --port 8000