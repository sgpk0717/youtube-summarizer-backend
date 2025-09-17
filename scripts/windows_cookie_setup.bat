@echo off
REM ========================================
REM   YouTube 쿠키 인증 설정
REM   Windows 환경
REM ========================================

echo ========================================
echo   YouTube 쿠키 인증 설정
echo   Windows 환경
echo ========================================
echo.

REM Python 환경 확인
echo [1/4] Python 환경 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았습니다
    echo https://www.python.org/downloads/ 에서 Python 3.7+ 설치하세요
    pause
    exit /b 1
)
python --version
echo.

REM yt-dlp 설치/업데이트
echo [2/4] yt-dlp 설치/업데이트 중...
pip install --upgrade yt-dlp
if errorlevel 1 (
    echo [ERROR] yt-dlp 설치 실패
    pause
    exit /b 1
)

REM yt-dlp 버전 확인
yt-dlp --version
echo.

REM Chrome 상태 확인
echo [3/4] Chrome 브라우저 상태 확인 중...
tasklist /FI "IMAGENAME eq chrome.exe" 2>nul | find /I /N "chrome.exe">nul
if "%ERRORLEVEL%"=="0" (
    echo.
    echo ╔═══════════════════════════════════════════════════════════╗
    echo ║           ⚠️  Chrome이 실행 중입니다!                      ║
    echo ╠═══════════════════════════════════════════════════════════╣
    echo ║  쿠키 추출을 위해 Chrome을 완전히 종료해야 합니다.        ║
    echo ║                                                            ║
    echo ║  1. Chrome 모든 창을 닫으세요                             ║
    echo ║  2. 시스템 트레이에서도 종료 확인                         ║
    echo ║  3. 작업 관리자에서 chrome.exe 프로세스 확인             ║
    echo ║                                                            ║
    echo ║  또는 Chrome 바로가기 속성에 다음을 추가하세요:           ║
    echo ║  --disable-features=LockProfileCookieDatabase             ║
    echo ╚═══════════════════════════════════════════════════════════╝
    echo.
    echo Chrome을 종료한 후 다시 실행하세요.
    pause
    exit /b 1
)
echo ✅ Chrome이 종료되어 있습니다.
echo.

REM 쿠키 테스트
echo [4/4] 쿠키 인증 테스트 중...
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                    사전 체크리스트                         ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  ✓ Chrome 브라우저에서 YouTube.com에 로그인되어 있나요?   ║
echo ║  ✓ 멤버십이 있는 계정으로 로그인했나요?                   ║
echo ║  ✓ Chrome이 완전히 종료되어 있나요?                       ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

echo 일반 영상으로 쿠키 테스트 중...
yt-dlp --cookies-from-browser chrome --skip-download --verbose "https://www.youtube.com/watch?v=jNQXAC9IVRw"

if errorlevel 1 (
    echo.
    echo ╔═══════════════════════════════════════════════════════════╗
    echo ║                    ❌ 쿠키 추출 실패                      ║
    echo ╠═══════════════════════════════════════════════════════════╣
    echo ║  가능한 원인:                                             ║
    echo ║  1. Chrome이 아직 실행 중                                 ║
    echo ║  2. Chrome에서 YouTube 로그인 안됨                        ║
    echo ║  3. Chrome 프로필 경로 문제                               ║
    echo ║                                                            ║
    echo ║  해결 방법:                                               ║
    echo ║  1. Chrome 완전 종료 후 재시도                           ║
    echo ║  2. Chrome에서 YouTube.com 로그인                         ║
    echo ║  3. Chrome 바로가기에 플래그 추가:                        ║
    echo ║     --disable-features=LockProfileCookieDatabase          ║
    echo ╚═══════════════════════════════════════════════════════════╝
    pause
    exit /b 1
)

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                  🎉 쿠키 인증 성공!                        ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM 선택적: 쿠키 파일로 저장
echo 쿠키를 파일로 저장하시겠습니까? (Y/N)
echo (Chrome이 켜져 있어도 사용 가능하게 됩니다)
choice /C YN /N
if errorlevel 2 goto SKIP_SAVE

echo.
echo 쿠키 파일 생성 중...
cd /d "%~dp0\.."
yt-dlp --cookies-from-browser chrome --cookies cookies.txt --skip-download "https://www.youtube.com/watch?v=jNQXAC9IVRw"

if exist cookies.txt (
    echo ✅ cookies.txt 파일이 생성되었습니다
    echo    이제 Chrome이 켜져 있어도 사용 가능합니다!
) else (
    echo ⚠️  쿠키 파일 생성 실패
)

:SKIP_SAVE
echo.
echo ========================================
echo   설정 완료!
echo.
echo   서버 시작: windows_run_server.bat
echo.
echo   팁: Chrome 바로가기에 다음 플래그 추가시
echo        Chrome 실행 중에도 사용 가능:
echo        --disable-features=LockProfileCookieDatabase
echo ========================================
echo.

pause