"""
YouTube 서비스 모듈
유튜브 영상 정보 및 자막 추출 담당
"""
from youtube_transcript_api import YouTubeTranscriptApi
import re
from typing import Optional, Tuple
import requests
from app.models.summary import VideoData
from app.utils.logger import LoggerMixin, setup_logger


class YouTubeService(LoggerMixin):
    """유튜브 관련 기능을 처리하는 서비스 클래스"""
    
    def __init__(self):
        # YouTube API 인스턴스 생성
        self.api = YouTubeTranscriptApi()
        self.log_info("🎬 YouTube 서비스 초기화 완료")
    
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
    
    def get_transcript_array(self):
        """
        마지막으로 가져온 타임스탬프별 자막 배열을 반환
        
        Returns:
            타임스탬프별 자막 배열 [{text, start, duration}, ...]
        """
        return getattr(self, '_last_transcript_array', [])
    
    async def get_video_data(self, url: str) -> VideoData:
        """
        비디오 정보와 자막을 가져옵니다.
        
        Args:
            url: 유튜브 영상 URL
            
        Returns:
            VideoData: 비디오 정보와 자막이 포함된 객체
        """
        self.log_info(f"📥 비디오 데이터 추출 시작", data={"url": url})
        
        # URL에서 비디오 ID 추출
        video_id = self.extract_video_id(url)
        
        # 자막 가져오기
        self.log_info(f"📝 자막 추출 시작: {video_id}")
        transcript_text, language = self._get_transcript(video_id)
        
        # 비디오 메타데이터 가져오기
        self.log_info(f"📊 비디오 메타데이터 추출 시작: {video_id}")
        video_info = self._get_video_info(video_id)
        
        result = VideoData(
            video_id=video_id,
            title=video_info["title"],
            channel=video_info["channel"],
            duration=video_info["duration"],
            transcript=transcript_text,
            language=language
        )
        
        self.log_info(f"✅ 비디오 데이터 추출 완료", data={
            "video_id": video_id,
            "title": video_info["title"],
            "channel": video_info["channel"],
            "language": language,
            "transcript_length": len(transcript_text) if transcript_text else 0
        })
        
        return result
    
    def _get_transcript(self, video_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        자막을 가져옵니다. 한국어 우선, 없으면 영어, 없으면 자동생성
        
        Args:
            video_id: 유튜브 비디오 ID
            
        Returns:
            (자막 텍스트, 언어 코드) 튜플
        """
        try:
            # 1. 한국어 자막 시도 (수동 + 자동 모두 포함)
            try:
                self.log_debug("🔍 한국어 자막 검색 중...")
                transcript_data = self.api.fetch(video_id, languages=['ko', 'ko-KR'])
                
                # 자막 텍스트 추출
                text = self._format_transcript(transcript_data)
                
                self.log_info(f"✅ 한국어 자막 발견", data={
                    "language": "ko",
                    "items_count": len(transcript_data),
                    "text_length": len(text),
                    "first_100_chars": text[:100] if text else ""
                })
                return text, "ko"
                
            except Exception as e:
                import traceback
                self.log_debug(f"한국어 자막 없음", data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                })
            
            # 2. 영어 자막 시도
            try:
                self.log_debug("🔍 영어 자막 검색 중...")
                transcript_data = self.api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
                
                # 자막 텍스트 추출
                text = self._format_transcript(transcript_data)
                
                self.log_info(f"✅ 영어 자막 발견", data={
                    "language": "en",
                    "items_count": len(transcript_data),
                    "text_length": len(text),
                    "first_100_chars": text[:100] if text else ""
                })
                return text, "en"
                
            except Exception as e:
                import traceback
                self.log_debug(f"영어 자막 없음", data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                })
            
            # 3. 사용 가능한 아무 자막이나 가져오기
            try:
                self.log_debug("🔍 사용 가능한 자막 검색 중...")
                
                # 사용 가능한 자막 목록 확인
                transcript_list = self.api.list(video_id)
                
                # 로깅을 위한 자막 정보 수집 - 더 상세한 정보 포함
                available_languages = []
                for transcript in transcript_list:
                    # 모든 속성 확인을 위한 디버깅
                    all_attributes = []
                    for attr in dir(transcript):
                        if not attr.startswith('_'):
                            try:
                                value = getattr(transcript, attr)
                                if not callable(value):
                                    all_attributes.append(f"{attr}={value}")
                            except:
                                pass
                    
                    lang_info = {
                        "language": getattr(transcript, 'language', 'unknown'),
                        "language_code": getattr(transcript, 'language_code', 'unknown'),
                        "is_generated": getattr(transcript, 'is_generated', False),
                        "is_translatable": getattr(transcript, 'is_translatable', False),
                        "all_attributes": all_attributes
                    }
                    available_languages.append(lang_info)
                    
                    # 개별 자막 상세 로그
                    self.log_debug(f"🔍 자막 상세 정보", data={
                        "language": lang_info["language"],
                        "language_code": lang_info["language_code"],
                        "is_generated": lang_info["is_generated"],
                        "is_translatable": lang_info["is_translatable"],
                        "all_attributes": lang_info["all_attributes"]
                    })
                
                self.log_info(f"📋 사용 가능한 자막 목록", data={
                    "video_id": video_id,
                    "total_count": len(available_languages),
                    "transcripts": available_languages
                })
                
                # 첫 번째 사용 가능한 자막 가져오기
                for transcript in transcript_list:
                    try:
                        language_code = getattr(transcript, 'language_code', 'unknown')
                        language_name = getattr(transcript, 'language', 'unknown')
                        is_generated = getattr(transcript, 'is_generated', False)
                        
                        self.log_debug(f"📥 자막 fetch 시도", data={
                            "language_code": language_code,
                            "language_name": language_name,
                            "is_generated": is_generated,
                            "is_translatable": getattr(transcript, 'is_translatable', False)
                        })
                        
                        transcript_data = transcript.fetch()
                        text = self._format_transcript(transcript_data)
                        
                        self.log_info(f"✅ 자막 발견", data={
                            "language": language_code,
                            "language_name": language_name,
                            "is_generated": is_generated,
                            "items_count": len(transcript_data),
                            "text_length": len(text),
                            "first_100_chars": text[:100] if text else ""
                        })
                        return text, language_code
                        
                    except Exception as e:
                        import traceback
                        self.log_error(f"❌ 자막 fetch 실패", data={
                            "language_code": language_code,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "traceback": traceback.format_exc()
                        })
                        continue
                
            except Exception as e:
                import traceback
                self.log_error(f"❌ 자막 목록 확인 실패", data={
                    "video_id": video_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                })
            
            self.log_warning("⚠️ 자막을 찾을 수 없음", data={"video_id": video_id})
            return None, None
                
        except Exception as e:
            import traceback
            self.log_error(f"❌ 자막 추출 오류", data={
                "video_id": video_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            })
            return None, None
    
    def _format_transcript(self, transcript_data) -> str:
        """
        자막 데이터를 텍스트로 변환하고 타임스탬프 배열 저장
        
        Args:
            transcript_data: fetch로 가져온 자막 데이터
            
        Returns:
            포맷된 자막 텍스트
        """
        # transcript_data는 FetchedTranscriptSnippet 객체들의 리스트
        # 각 객체는 text, start, duration 속성을 가짐
        text_parts = []
        transcript_array = []
        
        for item in transcript_data:
            # 객체의 속성들을 가져옴
            if hasattr(item, 'text'):
                text_parts.append(item.text)
                # 타임스탬프 배열 생성
                transcript_array.append({
                    "text": item.text,
                    "start": getattr(item, 'start', 0),
                    "duration": getattr(item, 'duration', 0)
                })
            elif isinstance(item, dict):
                text = item.get('text', '')
                text_parts.append(text)
                # 타임스탬프 배열 생성
                transcript_array.append({
                    "text": text,
                    "start": item.get('start', 0),
                    "duration": item.get('duration', 0)
                })
        
        # 타임스탬프 배열을 인스턴스 변수에 저장
        self._last_transcript_array = transcript_array
        
        self.log_debug(f"📦 타임스탬프 배열 생성", data={
            "array_length": len(transcript_array),
            "first_3_items": transcript_array[:3] if transcript_array else []
        })
        
        return ' '.join(text_parts)
    
    def _get_video_info(self, video_id: str) -> dict:
        """
        비디오 기본 정보를 가져옵니다.
        
        Args:
            video_id: 유튜브 비디오 ID
            
        Returns:
            비디오 정보 딕셔너리
        """
        # oembed API를 사용한 간단한 정보 추출
        try:
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            self.log_debug(f"📡 YouTube oembed API 호출", data={"url": url})
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.log_debug(f"📊 API 응답 수신", data=data)
                
                # title과 channel이 없으면 에러
                if not data.get("title") or not data.get("author_name"):
                    self.log_error("❌ 비디오 정보 불완전", data=data)
                    raise ValueError("비디오 정보가 불완전합니다")
                
                video_info = {
                    "title": data["title"],
                    "channel": data["author_name"],
                    "duration": "Unknown"  # oembed에서는 duration 제공 안 함
                }
                
                self.log_info(f"✅ 비디오 정보 추출 성공", data=video_info)
                return video_info
        except Exception as e:
            self.log_error(f"❌ 비디오 정보 가져오기 실패", data={"video_id": video_id, "error": str(e)})
            raise ValueError(f"비디오 정보를 가져올 수 없습니다: {str(e)}")
        
        # 참고: YouTube Data API를 사용하면 더 상세한 정보 가능
        # 하지만 API 키가 필요하고 할당량 제한이 있음
        # 필요시 아래 코드 사용:
        """
        # YouTube Data API 사용 (API 키 필요)
        import os
        from googleapiclient.discovery import build
        
        youtube = build('youtube', 'v3', developerKey=os.getenv('YOUTUBE_API_KEY'))
        request = youtube.videos().list(
            part="snippet,contentDetails",
            id=video_id
        )
        response = request.execute()
        
        if response['items']:
            item = response['items'][0]
            duration = item['contentDetails']['duration']  # ISO 8601 형식
            # PT15M33S -> 15:33 변환 필요
            return {
                "title": item['snippet']['title'],
                "channel": item['snippet']['channelTitle'],
                "duration": self._parse_duration(duration)
            }
        """