"""
YouTube 서비스 모듈 (yt-dlp 쿠키 버전)
멤버십 영상 자막 추출 지원
"""

import yt_dlp
import re
import json
import platform
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from app.models.summary import VideoData
from app.utils.logger import LoggerMixin


class YouTubeServiceYtDlp(LoggerMixin):
    """yt-dlp를 사용한 YouTube 서비스 클래스 (쿠키 인증)"""

    def __init__(self):
        """서비스 초기화"""
        self.cookie_method = self._determine_cookie_method()
        self.log_info("🚀 YouTube Service (yt-dlp) 초기화", data={
            "platform": platform.system(),
            "cookie_method": self._get_cookie_method_name()
        })

    def _determine_cookie_method(self) -> Dict:
        """최적의 쿠키 방법 결정"""
        # 1. 쿠키 파일이 있으면 우선 사용
        cookie_file = Path("cookies.txt")
        if cookie_file.exists():
            self.log_info("📁 쿠키 파일 발견, 파일 사용")
            return {"cookiefile": str(cookie_file)}

        # 2. Windows: Chrome 브라우저에서 직접 읽기
        # 주의: Chrome이 완전히 종료되어 있어야 함!
        if platform.system() == "Windows":
            self.log_info("🌐 Windows 환경, Chrome 브라우저에서 쿠키 읽기")
            return {"cookiesfrombrowser": ("chrome", None)}

        # 3. 기타 OS: Chrome 사용
        self.log_info("🌐 Chrome 브라우저에서 쿠키 읽기")
        return {"cookiesfrombrowser": ("chrome", None)}

    def _get_cookie_method_name(self) -> str:
        """쿠키 방법 이름 반환 (로깅용)"""
        if "cookiefile" in self.cookie_method:
            return f"cookie_file ({self.cookie_method['cookiefile']})"
        elif "cookiesfrombrowser" in self.cookie_method:
            browser = self.cookie_method["cookiesfrombrowser"][0]
            return f"browser ({browser})"
        return "unknown"

    def extract_video_id(self, url: str) -> str:
        """
        유튜브 URL에서 비디오 ID 추출

        Args:
            url: 유튜브 영상 URL

        Returns:
            비디오 ID 문자열

        Raises:
            ValueError: 유효하지 않은 URL
        """
        self.log_debug(f"📎 URL에서 비디오 ID 추출 시작", data={"url": url})

        # 다양한 유튜브 URL 형식 지원
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'(?:youtube\.com\/shorts\/)([^&\n?#]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                self.log_info(f"✅ 비디오 ID 추출 성공: {video_id}")
                return video_id

        self.log_error(f"❌ 유효하지 않은 URL", data={"url": url})
        raise ValueError("유효한 유튜브 URL이 아닙니다.")

    async def get_video_data(self, url: str) -> VideoData:
        """
        비디오 정보와 자막을 가져옵니다 (쿠키 사용)

        Args:
            url: 유튜브 영상 URL

        Returns:
            VideoData: 비디오 정보와 자막이 포함된 객체
        """
        self.log_info(f"📥 비디오 데이터 추출 시작", data={"url": url})

        # yt-dlp 옵션 설정
        ydl_opts = {
            **self.cookie_method,  # 쿠키 설정 적용

            # User-Agent 설정 (중요! 봇 감지 방지)
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # 자막 옵션
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['ko', 'en', 'ja', 'zh'],
            'skip_download': True,  # 영상은 다운로드하지 않음

            # 추출 옵션
            'extract_flat': False,
            'force_generic_extractor': False,

            # 출력 옵션
            'quiet': False,
            'no_warnings': False,

            # 후처리 옵션 (FFmpeg 없이)
            'postprocessors': [],

            # 로거 연결
            'logger': self._get_yt_dlp_logger(),

            # 진행 상황 후킹
            'progress_hooks': [self._progress_hook],

            # 속도 제한 (봇 감지 방지)
            'sleep_interval': 3,  # 다운로드 전 3초 대기
            'max_sleep_interval': 10,  # 최대 10초
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 영상 정보 추출
                self.log_info("🔍 영상 정보 추출 중...")
                info = ydl.extract_info(url, download=False)

                # 비디오 정보 추출
                video_id = info.get('id', '')
                title = info.get('title', '')
                channel = info.get('channel', info.get('uploader', ''))
                duration = info.get('duration', 0)

                # 멤버십 영상 확인
                availability = info.get('availability', '')
                is_membership = availability == 'subscriber_only'

                self.log_info(f"📊 영상 정보", data={
                    "video_id": video_id,
                    "title": title,
                    "channel": channel,
                    "duration": duration,
                    "availability": availability,
                    "is_membership": is_membership
                })

                # 자막 추출
                subtitle_text, language = self._extract_subtitles(info)

                # VideoData 객체 생성
                result = VideoData(
                    video_id=video_id,
                    title=title,
                    channel=channel,
                    duration=self._format_duration(duration),
                    transcript=subtitle_text,
                    language=language
                )

                self.log_info(f"✅ 비디오 데이터 추출 완료", data={
                    "video_id": video_id,
                    "title": title[:50],
                    "channel": channel,
                    "language": language,
                    "is_membership": is_membership,
                    "transcript_length": len(subtitle_text) if subtitle_text else 0
                })

                return result

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)

            # 에러 유형별 처리
            if "Sign in to confirm you're not a bot" in error_msg:
                self.log_error("🤖 봇 감지됨")
                raise Exception("봇 감지로 인한 접근 차단. OAuth2 재인증이 필요합니다.")

            elif "members-only" in error_msg or "subscriber_only" in error_msg:
                self.log_error("🔒 멤버십 권한 없음")
                raise Exception("이 영상은 채널 멤버십 가입이 필요합니다.")

            elif "Video unavailable" in error_msg:
                self.log_error("🚫 영상 사용 불가")
                raise Exception("영상을 사용할 수 없습니다. (삭제됨/비공개/지역 제한)")

            else:
                self.log_error(f"❌ 다운로드 오류: {error_msg}")
                raise Exception(f"영상 정보를 가져올 수 없습니다: {error_msg}")

        except Exception as e:
            self.log_error(f"❌ 예상치 못한 오류", data={
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise

    def _extract_subtitles(self, info: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        영상 정보에서 자막 추출

        Args:
            info: yt-dlp가 추출한 영상 정보

        Returns:
            (자막 텍스트, 언어 코드) 튜플
        """
        self.log_debug("📝 자막 추출 시작")

        # 수동 자막
        subtitles = info.get('subtitles', {})
        # 자동 생성 자막
        automatic_captions = info.get('automatic_captions', {})

        # 우선순위: 1. 한국어 자막, 2. 영어 자막, 3. 기타 언어
        language_priority = ['ko', 'en', 'ja', 'zh', 'zh-Hans', 'zh-Hant']

        # 수동 자막 우선 확인
        for lang in language_priority:
            if lang in subtitles:
                subtitle_text = self._download_subtitle(subtitles[lang], lang, is_auto=False)
                if subtitle_text:
                    return subtitle_text, lang

        # 자동 생성 자막 확인
        for lang in language_priority:
            if lang in automatic_captions:
                subtitle_text = self._download_subtitle(automatic_captions[lang], lang, is_auto=True)
                if subtitle_text:
                    return subtitle_text, f"{lang}-auto"

        # 아무 자막이나 가져오기
        if subtitles:
            lang = list(subtitles.keys())[0]
            subtitle_text = self._download_subtitle(subtitles[lang], lang, is_auto=False)
            if subtitle_text:
                return subtitle_text, lang

        if automatic_captions:
            lang = list(automatic_captions.keys())[0]
            subtitle_text = self._download_subtitle(automatic_captions[lang], lang, is_auto=True)
            if subtitle_text:
                return subtitle_text, f"{lang}-auto"

        self.log_warning("⚠️ 자막을 찾을 수 없음")
        return None, None

    def _download_subtitle(self, subtitle_entries: List[Dict], language: str, is_auto: bool) -> Optional[str]:
        """
        자막 엔트리에서 실제 자막 내용 다운로드

        Args:
            subtitle_entries: 자막 URL 정보 리스트
            language: 언어 코드
            is_auto: 자동 생성 자막 여부

        Returns:
            자막 텍스트 또는 None
        """
        if not subtitle_entries:
            return None

        subtitle_type = "자동 자막" if is_auto else "수동 자막"
        self.log_debug(f"📥 {subtitle_type} 다운로드 시도", data={"language": language})

        for entry in subtitle_entries:
            # JSON 형식 우선 (구조화된 데이터)
            if entry.get('ext') == 'json3':
                try:
                    import requests
                    response = requests.get(entry['url'], timeout=30)
                    response.raise_for_status()

                    # JSON3 형식 파싱
                    subtitle_data = response.json()
                    text = self._parse_json3_subtitle(subtitle_data)

                    self.log_info(f"✅ {subtitle_type} 다운로드 성공", data={
                        "language": language,
                        "format": "json3",
                        "length": len(text)
                    })
                    return text

                except Exception as e:
                    self.log_warning(f"JSON3 자막 파싱 실패: {str(e)}")
                    continue

            # VTT/SRT 형식
            elif entry.get('ext') in ['vtt', 'srt', 'srv1', 'srv2', 'srv3']:
                try:
                    import requests
                    response = requests.get(entry['url'], timeout=30)
                    response.raise_for_status()

                    text = self._parse_vtt_subtitle(response.text)

                    self.log_info(f"✅ {subtitle_type} 다운로드 성공", data={
                        "language": language,
                        "format": entry.get('ext'),
                        "length": len(text)
                    })
                    return text

                except Exception as e:
                    self.log_warning(f"VTT/SRT 자막 파싱 실패: {str(e)}")
                    continue

        return None

    def _parse_json3_subtitle(self, data: Dict) -> str:
        """JSON3 형식 자막 파싱"""
        text_parts = []

        try:
            events = data.get('events', [])
            for event in events:
                # 텍스트 세그먼트 추출
                if 'segs' in event:
                    for seg in event['segs']:
                        if 'utf8' in seg:
                            text_parts.append(seg['utf8'])
                elif 'text' in event:
                    text_parts.append(event['text'])
        except Exception as e:
            self.log_error(f"JSON3 파싱 오류: {str(e)}")

        return ' '.join(text_parts).strip()

    def _parse_vtt_subtitle(self, vtt_content: str) -> str:
        """VTT/SRT 형식 자막 파싱"""
        lines = vtt_content.split('\n')
        text_parts = []

        # 타임스탬프 패턴
        timestamp_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}')

        for line in lines:
            line = line.strip()
            # 헤더, 타임스탬프, 빈 줄 제외
            if line and not line.startswith('WEBVTT') and not timestamp_pattern.match(line) and not line.isdigit():
                # HTML 태그 제거
                clean_text = re.sub(r'<[^>]+>', '', line)
                if clean_text:
                    text_parts.append(clean_text)

        return ' '.join(text_parts).strip()

    def _format_duration(self, seconds: int) -> str:
        """초를 시:분:초 형식으로 변환"""
        if not seconds:
            return "Unknown"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    def _get_yt_dlp_logger(self):
        """yt-dlp용 로거 어댑터"""
        class YtDlpLogger:
            def __init__(self, parent):
                self.parent = parent

            def debug(self, msg):
                self.parent.log_debug(f"[yt-dlp] {msg}")

            def warning(self, msg):
                self.parent.log_warning(f"[yt-dlp] {msg}")

            def error(self, msg):
                self.parent.log_error(f"[yt-dlp] {msg}")

        return YtDlpLogger(self)

    def _progress_hook(self, d):
        """다운로드 진행 상황 후킹"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            self.log_debug(f"📊 진행률: {percent}")
        elif d['status'] == 'finished':
            self.log_debug("✅ 다운로드 완료")