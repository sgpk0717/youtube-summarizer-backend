@echo off
REM 쿠키 자동 업데이트 스크립트
REM 작업 스케줄러에 등록하여 매일 자동 실행

echo [%date% %time%] 쿠키 업데이트 시작 >> cookie_update_log.txt

REM Chrome 임시 종료
taskkill /F /IM chrome.exe 2>nul

REM 잠시 대기
timeout /t 2 /nobreak >nul

REM 쿠키 추출
cd /d "C:\youtube-summarizer-backend"
yt-dlp --cookies-from-browser chrome --cookies www.youtube.com_cookies.txt --skip-download "https://www.youtube.com/watch?v=jNQXAC9IVRw" 2>>cookie_update_log.txt

if %errorlevel% equ 0 (
    echo [%date% %time%] 쿠키 업데이트 성공 >> cookie_update_log.txt
) else (
    echo [%date% %time%] 쿠키 업데이트 실패 >> cookie_update_log.txt
)

REM Chrome 재시작 (선택사항)
REM start "" "C:\Program Files\Google\Chrome\Application\chrome.exe"

echo 쿠키가 업데이트되었습니다.