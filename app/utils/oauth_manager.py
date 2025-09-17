"""
OAuth2 토큰 관리 모듈
Windows PC에서 yt-dlp OAuth2 인증 관리
"""

import os
import json
import subprocess
import platform
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from app.utils.logger import LoggerMixin


class YtDlpOAuthManager(LoggerMixin):
    """yt-dlp OAuth2 토큰 관리 클래스"""

    def __init__(self):
        """OAuth2 매니저 초기화"""
        # Windows와 macOS 모두 지원
        if platform.system() == "Windows":
            self.cache_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'yt-dlp' / 'cache'
        else:  # macOS/Linux
            self.cache_dir = Path.home() / '.cache' / 'yt-dlp'

        self.token_file = self.cache_dir / 'youtube-oauth2.token_data'

        self.log_info(f"🔐 OAuth2 매니저 초기화", data={
            "platform": platform.system(),
            "cache_dir": str(self.cache_dir),
            "token_file": str(self.token_file)
        })

    def is_authenticated(self) -> bool:
        """OAuth2 인증 상태 확인"""
        exists = self.token_file.exists()
        self.log_debug(f"🔍 인증 상태 확인", data={
            "authenticated": exists,
            "token_file": str(self.token_file)
        })
        return exists

    def get_token_info(self) -> Dict:
        """토큰 정보 조회"""
        if not self.is_authenticated():
            self.log_warning("⚠️ 토큰 파일이 없음")
            return {}

        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)

            # 민감한 정보 마스킹
            safe_data = {}
            if 'access_token' in token_data:
                safe_data['access_token'] = "****" + token_data['access_token'][-10:]
            if 'refresh_token' in token_data:
                safe_data['refresh_token'] = "있음"
            if 'expires_at' in token_data:
                safe_data['expires_at'] = token_data['expires_at']
                expires = datetime.fromtimestamp(token_data['expires_at'])
                safe_data['expires_readable'] = expires.isoformat()
                safe_data['is_expired'] = expires < datetime.now()

            self.log_debug("📊 토큰 정보 조회", data=safe_data)
            return token_data

        except json.JSONDecodeError as e:
            self.log_error(f"❌ 토큰 파일 파싱 오류: {str(e)}")
            return {}
        except Exception as e:
            self.log_error(f"❌ 토큰 정보 조회 실패: {str(e)}")
            return {}

    def check_token_validity(self) -> Tuple[bool, str]:
        """토큰 유효성 확인"""
        if not self.is_authenticated():
            return False, "토큰 파일이 없습니다"

        token_info = self.get_token_info()
        if not token_info:
            return False, "토큰 파일이 손상되었습니다"

        # 만료 시간 확인
        if 'expires_at' in token_info:
            expires = datetime.fromtimestamp(token_info['expires_at'])
            if expires < datetime.now():
                # yt-dlp가 자동으로 refresh token으로 갱신하므로
                # 여기서는 경고만 표시
                self.log_warning("⚠️ 토큰이 만료되었으나 자동 갱신됩니다")
                return True, "토큰 만료 (자동 갱신 예정)"

        return True, "토큰 유효"

    def initialize_oauth(self) -> Tuple[bool, str]:
        """최초 OAuth2 인증 수행 (수동 프로세스)"""
        self.log_info("🚀 OAuth2 인증 프로세스 시작")

        # 이미 인증되어 있는지 확인
        if self.is_authenticated():
            self.log_info("✅ 이미 인증되어 있습니다")
            return True, "이미 인증되어 있습니다"

        # Windows에서는 수동 인증 필요
        if platform.system() == "Windows":
            message = """
            OAuth2 인증이 필요합니다:

            1. Windows PC에서 다음 명령 실행:
               yt-dlp --username oauth2 --password "" --verbose

            2. 표시되는 코드를 https://www.google.com/device 에 입력

            3. Google 계정으로 로그인 후 권한 승인

            4. 인증 완료 후 서버를 재시작하세요
            """
            self.log_warning("⚠️ 수동 OAuth2 인증 필요", data={"message": message})
            return False, message

        # macOS/Linux에서 테스트용
        try:
            result = subprocess.run(
                ['yt-dlp', '--username', 'oauth2', '--password', '', '--verbose'],
                capture_output=True,
                text=True,
                timeout=300  # 5분 타임아웃
            )

            if result.returncode == 0:
                self.log_info("✅ OAuth2 인증 성공")
                return True, "OAuth2 인증 성공"
            else:
                self.log_error(f"❌ OAuth2 인증 실패: {result.stderr}")
                return False, result.stderr

        except subprocess.TimeoutExpired:
            self.log_error("❌ 인증 시간 초과")
            return False, "인증 시간 초과 (5분)"
        except FileNotFoundError:
            self.log_error("❌ yt-dlp가 설치되지 않음")
            return False, "yt-dlp가 설치되지 않았습니다"
        except Exception as e:
            self.log_error(f"❌ 인증 오류: {str(e)}")
            return False, f"인증 오류: {str(e)}"

    def get_ydl_opts(self, additional_opts: Optional[Dict] = None) -> Dict:
        """yt-dlp 옵션 생성 (OAuth2 포함)"""
        base_opts = {
            # OAuth2 인증
            'username': 'oauth2',
            'password': '',

            # 캐시 디렉토리
            'cachedir': str(self.cache_dir),

            # 기본 옵션
            'quiet': False,
            'no_warnings': False,
            'verbose': True,
        }

        # 추가 옵션 병합
        if additional_opts:
            base_opts.update(additional_opts)

        self.log_debug("🔧 yt-dlp 옵션 생성", data={
            "cache_dir": str(self.cache_dir),
            "has_additional_opts": bool(additional_opts)
        })

        return base_opts

    def clear_cache(self) -> bool:
        """OAuth2 캐시 삭제 (로그아웃)"""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
                self.log_info("✅ OAuth2 토큰 삭제됨")

            # 전체 캐시 디렉토리 삭제 옵션
            # import shutil
            # if self.cache_dir.exists():
            #     shutil.rmtree(self.cache_dir)

            return True
        except Exception as e:
            self.log_error(f"❌ 캐시 삭제 실패: {str(e)}")
            return False

    def get_status_summary(self) -> Dict:
        """인증 상태 요약 정보"""
        is_auth = self.is_authenticated()
        valid, message = self.check_token_validity()

        summary = {
            "authenticated": is_auth,
            "valid": valid,
            "message": message,
            "cache_dir": str(self.cache_dir),
            "token_exists": self.token_file.exists(),
            "platform": platform.system()
        }

        # 토큰 정보 추가 (안전한 정보만)
        if is_auth:
            token_info = self.get_token_info()
            if 'expires_at' in token_info:
                expires = datetime.fromtimestamp(token_info['expires_at'])
                summary["expires_at"] = expires.isoformat()
                summary["expires_in_hours"] = (expires - datetime.now()).total_seconds() / 3600

        self.log_info("📊 OAuth2 상태 요약", data=summary)
        return summary