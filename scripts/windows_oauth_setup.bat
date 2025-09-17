@echo off
REM ========================================
REM   YouTube OAuth2 초기 설정
REM   Windows 환경
REM ========================================

echo ========================================
echo   YouTube OAuth2 인증 설정
echo   Windows 환경
echo ========================================
echo.

REM Python 환경 확인
echo [1/5] Python 환경 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았습니다
    echo https://www.python.org/downloads/ 에서 Python 3.7+ 설치하세요
    pause
    exit /b 1
)
python --version
echo.

REM FFmpeg 확인 (선택사항)
echo [2/5] FFmpeg 확인 중...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg가 설치되지 않았습니다
    echo 자막 변환 기능이 제한될 수 있습니다
    echo https://ffmpeg.org/download.html 에서 설치 가능
) else (
    echo FFmpeg 설치 확인됨
)
echo.

REM yt-dlp 설치/업데이트
echo [3/5] yt-dlp 설치/업데이트 중...
pip install --upgrade yt-dlp
if errorlevel 1 (
    echo [ERROR] yt-dlp 설치 실패
    pause
    exit /b 1
)

REM yt-dlp 버전 확인
yt-dlp --version
echo.

REM 요구사항 설치
echo [4/5] Python 패키지 설치 중...
cd /d "%~dp0\.."
if exist requirements.txt (
    pip install -r requirements.txt --quiet
    echo 패키지 설치 완료
) else (
    echo [WARNING] requirements.txt를 찾을 수 없습니다
    echo 수동으로 다음 패키지를 설치하세요:
    echo   pip install fastapi uvicorn yt-dlp openai python-dotenv
)
echo.

REM OAuth2 인증 시작
echo [5/5] OAuth2 인증을 시작합니다...
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                    OAuth2 인증 절차                        ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  1. 아래 명령이 실행되면 코드가 표시됩니다 (XXX-YYY-ZZZ)  ║
echo ║                                                            ║
echo ║  2. 브라우저에서 https://www.google.com/device 접속       ║
echo ║                                                            ║
echo ║  3. 표시된 코드를 입력하세요                              ║
echo ║                                                            ║
echo ║  4. Google 계정으로 로그인                                ║
echo ║                                                            ║
echo ║  5. "YouTube on TV" 권한 승인                            ║
echo ║                                                            ║
echo ║  ※ 주의: 멤버십이 있는 Google 계정으로 로그인하세요      ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

pause

REM OAuth2 인증 실행
echo.
echo OAuth2 인증을 시작합니다...
yt-dlp --username oauth2 --password "" --verbose https://www.youtube.com/watch?v=jNQXAC9IVRw

if errorlevel 1 (
    echo.
    echo ╔═══════════════════════════════════════════════════════════╗
    echo ║                    인증 실패                              ║
    echo ╠═══════════════════════════════════════════════════════════╣
    echo ║  가능한 원인:                                             ║
    echo ║  1. 인터넷 연결 문제                                      ║
    echo ║  2. 코드 입력 시간 초과                                   ║
    echo ║  3. 권한 승인 거부                                        ║
    echo ║                                                            ║
    echo ║  다시 시도하려면 이 스크립트를 재실행하세요              ║
    echo ╚═══════════════════════════════════════════════════════════╝
    pause
    exit /b 1
)

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                  🎉 인증 성공!                            ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM 캐시 디렉토리 확인
echo 토큰 저장 위치 확인 중...
dir "%LOCALAPPDATA%\yt-dlp\cache\youtube-oauth2.*" 2>nul

if exist "%LOCALAPPDATA%\yt-dlp\cache\youtube-oauth2.token_data" (
    echo.
    echo ✅ OAuth2 토큰이 정상적으로 저장되었습니다
    echo 📁 위치: %LOCALAPPDATA%\yt-dlp\cache\
) else (
    echo.
    echo ⚠️  토큰 파일을 찾을 수 없습니다
    echo 인증이 실패했을 수 있습니다
)

echo.
echo ========================================
echo   설정 완료!
echo   이제 서버를 시작할 수 있습니다.
echo
echo   서버 시작: windows_run_server.bat
echo ========================================
echo.

REM OAuth2 상태 확인
echo OAuth2 상태 확인 중...
cd scripts
if exist check_oauth_status.py (
    python check_oauth_status.py
)

pause