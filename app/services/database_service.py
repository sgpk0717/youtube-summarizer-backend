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
                "channel": video_data.channel,
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
                query_builder = query_builder.eq("channel", channel)
            
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
                .select("video_id, title, channel, language_code, access_count, created_at")\
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

    async def save_multi_agent_report(
        self,
        user_id: str,
        video_id: str,
        title: str,
        channel: str,
        duration: Optional[float],
        language: Optional[str],
        final_report: Optional[str],
        agent_results: Dict[str, Any],
        processing_status: Dict[str, Any]
    ) -> Optional[str]:
        """
        멀티에이전트 분석 보고서 저장

        Args:
            user_id: 사용자 ID
            video_id: YouTube 비디오 ID
            title: 비디오 제목
            channel: 채널명
            duration: 비디오 길이(초)
            language: 비디오 언어
            final_report: 최종 분석 보고서
            agent_results: 에이전트별 분석 결과
            processing_status: 처리 상태 정보

        Returns:
            저장된 보고서 ID 또는 None
        """
        try:
            self.log_info(f"🤖 멀티에이전트 보고서 저장 시작", data={
                "user_id": user_id,
                "video_id": video_id,
                "title": title
            })

            # 1. analysis_reports 테이블에 메인 레코드 저장
            # 닉네임을 UUID로 변환
            actual_user_id = await self._get_or_create_user_id(user_id)
            self.log_info(f"👤 닉네임을 UUID로 변환", data={
                "nickname": user_id,
                "user_uuid": actual_user_id
            })

            report_data = {
                "video_id": video_id,
                "title": title,
                "channel": channel,  # 테이블 컬럼명과 일치하도록 수정
                "duration": duration,
                "language": language,
                "analysis_result": {
                    "agent_results": agent_results,
                    "processing_status": processing_status
                },
                "final_report": final_report,
                "transcript_available": True,
                "analysis_type": "multi_agent",
                "processing_time": processing_status.get("total_processing_time")
            }

            # user_id가 있으면 포함
            if actual_user_id:
                report_data["user_id"] = actual_user_id

            self.log_debug(f"📤 저장할 보고서 데이터", data=report_data)

            # 보고서 삽입
            report_response = self.client.table("analysis_reports")\
                .insert(report_data)\
                .execute()

            if not report_response.data or len(report_response.data) == 0:
                self.log_error("❌ 보고서 저장 실패 - 응답 없음")
                return None

            report_id = report_response.data[0]["id"]
            self.log_info(f"✅ 보고서 메인 레코드 저장 완료", data={"report_id": report_id})

            # 2. agent_results 테이블에 각 에이전트 결과 저장
            agent_records = []

            # 각 에이전트 결과 저장
            for agent_type in ['transcript_refinement', 'speaker_diarization', 'topic_cohesion', 'structure_design', 'report_synthesis']:
                agent_data = agent_results.get(agent_type, {})

                if agent_data and agent_data.get("success"):
                    agent_record = {
                        "report_id": report_id,
                        "agent_type": agent_type,
                        "result_data": agent_data.get("result", {}),
                        "processing_time": agent_data.get("processing_time", 0),
                        "success": True
                    }
                    agent_records.append(agent_record)
                    self.log_debug(f"📊 {agent_type} 에이전트 결과 준비", data={
                        "success": True,
                        "has_data": bool(agent_data.get("result"))
                    })

            # 에이전트 결과들 한번에 삽입
            if agent_records:
                self.log_info(f"📤 {len(agent_records)}개 에이전트 결과 저장 시작")

                agent_response = self.client.table("agent_results")\
                    .insert(agent_records)\
                    .execute()

                if agent_response.data:
                    self.log_info(f"✅ 에이전트 결과 저장 성공", data={
                        "report_id": report_id,
                        "agent_count": len(agent_records)
                    })
                else:
                    self.log_warning("⚠️ 에이전트 결과 저장 실패 - 보고서는 저장됨")
            else:
                self.log_warning("⚠️ 저장할 에이전트 결과 없음")

            return report_id

        except Exception as e:
            self.log_error(f"❌ 멀티에이전트 보고서 저장 실패", data={
                "user_id": user_id,
                "video_id": video_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return None

    async def _get_or_create_user_id(self, nickname: str) -> str:
        """
        닉네임으로 사용자 UUID 조회 또는 생성

        Args:
            nickname: 사용자 닉네임

        Returns:
            사용자 UUID
        """
        try:
            # 기존 사용자 검색
            result = self.client.table('nicknames')\
                .select('id')\
                .ilike('nickname', nickname)\
                .execute()

            if result.data:
                user_uuid = result.data[0]['id']
                self.log_info(f"✅ 기존 사용자 발견", data={
                    "nickname": nickname,
                    "uuid": user_uuid
                })
                return user_uuid
            else:
                # 새 사용자 생성
                import uuid
                new_user = {
                    "nickname": nickname
                }
                result = self.client.table('nicknames').insert(new_user).execute()
                user_uuid = result.data[0]['id']

                self.log_info(f"✅ 새 사용자 생성", data={
                    "nickname": nickname,
                    "uuid": user_uuid
                })
                return user_uuid

        except Exception as e:
            self.log_error(f"❌ 사용자 ID 조회/생성 실패", data={
                "nickname": nickname,
                "error": str(e)
            })
            # 임시로 닉네임 직접 사용 (호환성 유지)
            return nickname

    async def get_user_reports(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        사용자별 분석 보고서 목록 조회

        Args:
            user_id: 사용자 ID (닉네임)
            limit: 결과 제한 수

        Returns:
            보고서 목록
        """
        try:
            self.log_info(f"📚 사용자 보고서 목록 조회", data={
                "user_id": user_id,
                "limit": limit
            })

            # 닉네임을 UUID로 변환
            actual_user_id = await self._get_or_create_user_id(user_id)

            response = self.client.table("analysis_reports")\
                .select("*")\
                .eq("user_id", actual_user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()

            if response.data:
                self.log_info(f"✅ 보고서 목록 조회 성공", data={
                    "user_id": user_id,
                    "count": len(response.data)
                })
                return response.data
            else:
                self.log_info("ℹ️ 보고서 없음")
                return []

        except Exception as e:
            self.log_error(f"❌ 보고서 목록 조회 실패", data={
                "user_id": user_id,
                "error": str(e)
            })
            return []

    async def get_report_with_agents(
        self,
        report_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        보고서와 에이전트 결과 상세 조회

        Args:
            report_id: 보고서 ID

        Returns:
            보고서 상세 정보 (에이전트 결과 포함)
        """
        try:
            self.log_info(f"📖 보고서 상세 조회", data={"report_id": report_id})

            # 보고서 메인 정보 조회
            report_response = self.client.table("analysis_reports")\
                .select("*")\
                .eq("id", report_id)\
                .execute()

            if not report_response.data or len(report_response.data) == 0:
                self.log_warning(f"⚠️ 보고서 없음: {report_id}")
                return None

            report = report_response.data[0]

            # 에이전트 결과 조회
            agent_response = self.client.table("agent_results")\
                .select("*")\
                .eq("report_id", report_id)\
                .execute()

            # 에이전트 결과를 딕셔너리로 변환
            agent_results = {}
            if agent_response.data:
                for agent in agent_response.data:
                    agent_results[agent["agent_type"]] = {
                        "success": agent["success"],
                        "result": agent["result_data"],
                        "processing_time": agent["processing_time"]
                    }

            # 보고서에 에이전트 결과 추가
            report["agent_results"] = agent_results

            self.log_info(f"✅ 보고서 상세 조회 성공", data={
                "report_id": report_id,
                "agent_count": len(agent_results)
            })

            return report

        except Exception as e:
            self.log_error(f"❌ 보고서 상세 조회 실패", data={
                "report_id": report_id,
                "error": str(e)
            })
            return None