"""
Supabase 데이터베이스 서비스 모듈
비디오 정보와 자막을 저장하고 조회하는 기능
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client
from app.utils.logger import LoggerMixin
from app.models.summary import VideoData, Summary


class DatabaseService(LoggerMixin):
    """Supabase 데이터베이스 서비스 클래스"""
    
    def __init__(self):
        """Supabase 클라이언트 초기화"""
        # 환경 변수에서 Supabase 설정 가져오기
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            self.log_error("❌ Supabase 설정 누락")
            raise ValueError("SUPABASE_URL과 SUPABASE_ANON_KEY 환경 변수가 필요합니다.")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        self.log_info("🗄️ Supabase 데이터베이스 서비스 초기화 완료")
    
    async def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        비디오 정보를 데이터베이스에서 조회
        
        Args:
            video_id: YouTube 비디오 ID
            
        Returns:
            비디오 정보 딕셔너리 또는 None
        """
        try:
            self.log_info(f"📖 비디오 조회 시작: {video_id}")
            
            # 데이터 조회
            response = self.client.table("videos")\
                .select("*")\
                .eq("video_id", video_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                video_data = response.data[0]
                
                # 조회수 증가 및 마지막 접근 시간 업데이트
                self.client.rpc("increment_video_access", {"p_video_id": video_id}).execute()
                
                self.log_info(f"✅ 비디오 조회 성공", data={
                    "video_id": video_id,
                    "title": video_data.get("title"),
                    "access_count": video_data.get("access_count")
                })
                
                return video_data
            else:
                self.log_info(f"ℹ️ 비디오 없음: {video_id}")
                return None
                
        except Exception as e:
            self.log_error(f"❌ 비디오 조회 실패", data={
                "video_id": video_id,
                "error": str(e)
            })
            return None
    
    async def save_video(
        self, 
        video_data: VideoData,
        summary: Summary,
        transcript_array: List[Dict[str, Any]]
    ) -> bool:
        """
        비디오 정보와 자막을 데이터베이스에 저장
        
        Args:
            video_data: 비디오 메타데이터
            summary: 요약 정보
            transcript_array: 타임스탬프별 자막 배열
            
        Returns:
            저장 성공 여부
        """
        try:
            self.log_info(f"💾 비디오 저장 시작: {video_data.video_id}")
            
            # 저장할 데이터 준비
            data = {
                "video_id": video_data.video_id,
                "title": video_data.title,
                "channel_name": video_data.channel,
                "duration": video_data.duration,
                "transcript_text": video_data.transcript,
                "transcript_json": transcript_array,  # [{text: "", start: 0, duration: 0}, ...]
                "language_code": video_data.language,
                "is_auto_generated": True,  # 현재는 자동 생성 자막만 지원
                "summary_brief": summary.brief,
                "summary_key_points": summary.key_points,
                "summary_detailed": summary.detailed,
            }
            
            # 로깅 (전문)
            self.log_debug(f"📤 저장할 데이터", data=data)
            
            # 기존 데이터 확인
            existing = await self.get_video(video_data.video_id)
            
            if existing:
                # 업데이트
                self.log_info(f"🔄 기존 데이터 업데이트: {video_data.video_id}")
                response = self.client.table("videos")\
                    .update(data)\
                    .eq("video_id", video_data.video_id)\
                    .execute()
            else:
                # 새로 삽입
                self.log_info(f"➕ 새 데이터 삽입: {video_data.video_id}")
                response = self.client.table("videos")\
                    .insert(data)\
                    .execute()
            
            if response.data:
                self.log_info(f"✅ 비디오 저장 성공", data={
                    "video_id": video_data.video_id,
                    "title": video_data.title,
                    "transcript_length": len(video_data.transcript) if video_data.transcript else 0
                })
                return True
            else:
                self.log_error(f"❌ 비디오 저장 실패 - 응답 없음", data={
                    "video_id": video_data.video_id
                })
                return False
                
        except Exception as e:
            self.log_error(f"❌ 비디오 저장 실패", data={
                "video_id": video_data.video_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False
    
    async def search_videos(
        self, 
        query: Optional[str] = None,
        channel: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        비디오 검색
        
        Args:
            query: 검색어 (제목 또는 자막에서 검색)
            channel: 채널명 필터
            language: 언어 코드 필터
            limit: 결과 제한 수
            
        Returns:
            검색 결과 리스트
        """
        try:
            self.log_info(f"🔍 비디오 검색 시작", data={
                "query": query,
                "channel": channel,
                "language": language,
                "limit": limit
            })
            
            # 기본 쿼리
            query_builder = self.client.table("videos").select("*")
            
            # 필터 적용
            if channel:
                query_builder = query_builder.eq("channel_name", channel)
            
            if language:
                query_builder = query_builder.eq("language_code", language)
            
            if query:
                # 제목이나 자막에서 검색 (PostgreSQL의 ILIKE 사용)
                query_builder = query_builder.or_(
                    f"title.ilike.%{query}%,transcript_text.ilike.%{query}%"
                )
            
            # 정렬 및 제한
            query_builder = query_builder.order("created_at", desc=True).limit(limit)
            
            # 실행
            response = query_builder.execute()
            
            if response.data:
                self.log_info(f"✅ 검색 완료", data={
                    "result_count": len(response.data)
                })
                return response.data
            else:
                self.log_info("ℹ️ 검색 결과 없음")
                return []
                
        except Exception as e:
            self.log_error(f"❌ 비디오 검색 실패", data={
                "error": str(e)
            })
            return []
    
    async def get_popular_videos(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        인기 비디오 조회 (조회수 기준)
        
        Args:
            limit: 결과 제한 수
            
        Returns:
            인기 비디오 리스트
        """
        try:
            self.log_info(f"🌟 인기 비디오 조회 시작")
            
            response = self.client.table("videos")\
                .select("video_id, title, channel_name, language_code, access_count, created_at")\
                .order("access_count", desc=True)\
                .limit(limit)\
                .execute()
            
            if response.data:
                self.log_info(f"✅ 인기 비디오 조회 성공", data={
                    "count": len(response.data)
                })
                return response.data
            else:
                return []
                
        except Exception as e:
            self.log_error(f"❌ 인기 비디오 조회 실패", data={
                "error": str(e)
            })
            return []