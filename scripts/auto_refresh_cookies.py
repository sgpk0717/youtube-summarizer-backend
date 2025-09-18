"""
YouTube 쿠키 자동 갱신 스크립트
매일 실행하거나 서버 시작 시 실행
"""
import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

def refresh_cookies():
    """Chrome에서 쿠키를 추출하여 파일로 저장"""
    print(f"[{datetime.now()}] 쿠키 갱신 시작...")

    # Chrome 프로세스 확인
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq chrome.exe'],
                              capture_output=True, text=True)
        chrome_running = 'chrome.exe' in result.stdout

        if chrome_running:
            print("⚠️  Chrome이 실행 중입니다. 종료 시도...")
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'],
                         capture_output=True)
            time.sleep(2)
    except:
        pass

    # 쿠키 추출
    cookie_file = Path(__file__).parent.parent / "www.youtube.com_cookies.txt"

    try:
        cmd = [
            'yt-dlp',
            '--cookies-from-browser', 'chrome',
            '--cookies', str(cookie_file),
            '--skip-download',
            'https://www.youtube.com/watch?v=jNQXAC9IVRw'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ 쿠키 갱신 성공: {cookie_file}")
            return True
        else:
            print(f"❌ 쿠키 갱신 실패: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def check_cookie_age():
    """쿠키 파일 나이 확인 (24시간 이상이면 갱신 권장)"""
    cookie_file = Path(__file__).parent.parent / "www.youtube.com_cookies.txt"

    if cookie_file.exists():
        mtime = os.path.getmtime(cookie_file)
        age_hours = (time.time() - mtime) / 3600

        print(f"📁 쿠키 파일 나이: {age_hours:.1f}시간")

        if age_hours > 24:
            print("⚠️  쿠키가 24시간 이상 되었습니다. 갱신을 권장합니다.")
            return True
    else:
        print("❌ 쿠키 파일이 없습니다.")
        return True

    return False

if __name__ == "__main__":
    # 쿠키 나이 확인
    if check_cookie_age():
        # 자동 갱신
        if refresh_cookies():
            print("🎉 쿠키 자동 갱신 완료!")
        else:
            print("⚠️  수동으로 쿠키를 갱신해주세요.")
    else:
        print("✅ 쿠키가 최신 상태입니다.")