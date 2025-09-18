"""
조건부 쿠키 갱신 시스템
API 요청 시점에 필요한 경우에만 갱신
"""
import os
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from app.utils.logger import LoggerMixin


class CookieRefresher(LoggerMixin):
    """쿠키 자동 갱신 관리 클래스"""

    def __init__(self, cookie_file: str = "www.youtube.com_cookies.txt"):
        self.cookie_file = Path(cookie_file)
        self.last_refresh_time: Optional[float] = None
        self.refresh_interval = 600  # 10분 (600초)
        self.refresh_count = 0

        # 쿠키 파일이 있으면 마지막 수정 시간을 초기값으로
        if self.cookie_file.exists():
            self.last_refresh_time = os.path.getmtime(self.cookie_file)
            self.log_info(f"🍪 기존 쿠키 파일 감지", data={
                "file": str(self.cookie_file),
                "age_minutes": self._get_cookie_age_minutes()
            })

    def _get_cookie_age_minutes(self) -> float:
        """쿠키 나이를 분 단위로 반환"""
        if not self.last_refresh_time:
            return float('inf')
        age_seconds = time.time() - self.last_refresh_time
        return age_seconds / 60

    def should_refresh(self) -> bool:
        """쿠키 갱신이 필요한지 확인"""
        # 쿠키 파일이 없으면 갱신 필요
        if not self.cookie_file.exists():
            self.log_warning("⚠️ 쿠키 파일이 없음, 갱신 필요")
            return True

        # 마지막 갱신 시간이 없으면 갱신 필요
        if not self.last_refresh_time:
            self.log_warning("⚠️ 갱신 기록 없음, 갱신 필요")
            return True

        # 경과 시간 확인
        elapsed = time.time() - self.last_refresh_time
        age_minutes = elapsed / 60

        # 10분 이상 경과했으면 갱신
        needs_refresh = elapsed > self.refresh_interval

        self.log_debug(f"🕐 쿠키 상태 확인", data={
            "age_minutes": f"{age_minutes:.1f}",
            "threshold_minutes": self.refresh_interval / 60,
            "needs_refresh": needs_refresh
        })

        return needs_refresh

    def refresh_cookies(self) -> bool:
        """yt-dlp를 사용해 쿠키 갱신"""
        try:
            self.log_info("🔄 쿠키 갱신 시작...")

            # Chrome 프로세스 확인 (선택사항)
            # Chrome이 켜져 있으면 건너뛰기
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq chrome.exe'],
                capture_output=True,
                text=True,
                shell=True
            )

            if 'chrome.exe' in result.stdout:
                self.log_warning("⚠️ Chrome이 실행 중, 기존 쿠키 사용")
                # Chrome 실행 중이면 갱신하지 않고 기존 쿠키 사용
                return False

            # yt-dlp로 쿠키 추출
            cmd = [
                'yt-dlp',
                '--cookies-from-browser', 'chrome',
                '--cookies', str(self.cookie_file),
                '--skip-download',
                'https://www.youtube.com/watch?v=jNQXAC9IVRw'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            if result.returncode == 0:
                self.last_refresh_time = time.time()
                self.refresh_count += 1

                self.log_info(f"✅ 쿠키 갱신 성공", data={
                    "file": str(self.cookie_file),
                    "refresh_count": self.refresh_count,
                    "timestamp": datetime.now().isoformat()
                })
                return True
            else:
                self.log_error(f"❌ 쿠키 갱신 실패", data={
                    "error": result.stderr
                })
                return False

        except Exception as e:
            self.log_error(f"❌ 쿠키 갱신 중 예외 발생", data={
                "error": str(e)
            })
            return False

    async def ensure_fresh_cookies(self) -> bool:
        """
        쿠키가 신선한지 확인하고 필요시 갱신
        API 요청 전에 호출
        """
        if self.should_refresh():
            self.log_info("🍪 쿠키 갱신이 필요합니다")
            success = self.refresh_cookies()

            if not success:
                # 갱신 실패해도 기존 쿠키로 계속 진행
                self.log_warning("⚠️ 갱신 실패, 기존 쿠키 사용")

            return success
        else:
            age = self._get_cookie_age_minutes()
            self.log_debug(f"✅ 쿠키가 아직 신선함 ({age:.1f}분)")
            return True

    def get_status(self) -> dict:
        """현재 쿠키 상태 반환"""
        exists = self.cookie_file.exists()
        age_minutes = self._get_cookie_age_minutes() if exists else None

        return {
            "cookie_file": str(self.cookie_file),
            "exists": exists,
            "age_minutes": age_minutes,
            "needs_refresh": self.should_refresh(),
            "refresh_count": self.refresh_count,
            "last_refresh": datetime.fromtimestamp(self.last_refresh_time).isoformat()
                           if self.last_refresh_time else None
        }


# 싱글톤 인스턴스
_cookie_refresher = None

def get_cookie_refresher() -> CookieRefresher:
    """싱글톤 CookieRefresher 인스턴스 반환"""
    global _cookie_refresher
    if _cookie_refresher is None:
        _cookie_refresher = CookieRefresher()
    return _cookie_refresher