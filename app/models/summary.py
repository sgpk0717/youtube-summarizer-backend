"""
데이터 모델 정의
Pydantic을 사용한 요청/응답 모델
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SummarizeRequest(BaseModel):
    """요약 요청 모델"""
    url: str = Field(..., description="유튜브 영상 URL", example="https://youtube.com/watch?v=dQw4w9WgXcQ")


class Summary(BaseModel):
    """요약 정보 모델"""
    brief: str = Field(..., description="한 줄 요약 (50자 이내)")
    key_points: List[str] = Field(..., description="핵심 포인트 리스트 (3-5개)")
    detailed: str = Field(..., description="상세 요약 (500자 이내)")


class SummaryResponse(BaseModel):
    """요약 응답 모델"""
    video_id: str = Field(..., description="유튜브 비디오 ID")
    title: str = Field(..., description="영상 제목")
    channel: str = Field(..., description="채널명")
    duration: str = Field(..., description="영상 길이")
    language: Optional[str] = Field(None, description="자막 언어 코드")
    summary: Summary = Field(..., description="요약 내용")
    transcript_available: bool = Field(..., description="자막 사용 가능 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "title": "샘플 영상 제목",
                "channel": "샘플 채널",
                "duration": "3:52",
                "language": "ko",
                "summary": {
                    "brief": "이 영상은 샘플 요약입니다.",
                    "key_points": [
                        "첫 번째 핵심 포인트",
                        "두 번째 핵심 포인트",
                        "세 번째 핵심 포인트"
                    ],
                    "detailed": "영상의 상세한 내용을 요약한 텍스트입니다. 주요 내용과 맥락을 포함합니다."
                },
                "transcript_available": True
            }
        }


class VideoData(BaseModel):
    """비디오 데이터 모델 (내부 사용)"""
    video_id: str
    title: str
    channel: str
    duration: str
    transcript: Optional[str] = None
    language: Optional[str] = None


# 멀티에이전트 관련 모델들 (간소화된 버전)
class MultiAgentAnalyzeRequest(BaseModel):
    """멀티에이전트 분석 요청 모델"""
    url: str = Field(..., description="유튜브 영상 URL", example="https://youtube.com/watch?v=dQw4w9WgXcQ")
    enable_caching: bool = Field(default=True, description="캐싱 활성화 여부")


class MultiAgentAnalyzeResponse(BaseModel):
    """멀티에이전트 분석 응답 모델"""
    # 기본 비디오 정보
    video_id: str = Field(..., description="유튜브 비디오 ID")
    title: str = Field(..., description="영상 제목")
    channel: str = Field(..., description="채널명")
    duration: str = Field(..., description="영상 길이")
    language: Optional[str] = Field(None, description="자막 언어 코드")
    
    # 멀티에이전트 분석 결과
    analysis_result: Dict[str, Any] = Field(..., description="멀티에이전트 분석 결과")
    
    # 최종 보고서 (편의성을 위해 최상위에도 포함)
    final_report: Optional[str] = Field(None, description="최종 종합 분석 보고서")
    
    # 메타데이터
    transcript_available: bool = Field(..., description="자막 사용 가능 여부")
    analysis_type: str = Field(default="multi_agent", description="분석 유형")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "title": "샘플 영상 제목",
                "channel": "샘플 채널",
                "duration": "3:52",
                "language": "ko",
                "analysis_result": {
                    "processing_status": {
                        "status": "completed",
                        "completed_agents": ["transcript_refiner", "speaker_diarizer", "topic_cohesion", "structure_designer", "report_synthesizer"],
                        "total_processing_time": 120.5
                    },
                    "total_agents": 5,
                    "successful_agents": 5
                },
                "final_report": "# 종합 분석 보고서\\n\\n## 개요\\n...",
                "transcript_available": True,
                "analysis_type": "multi_agent",
                "processing_time": 120.5
            }
        }


class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    error: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[str] = Field(None, description="상세 정보")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "NO_TRANSCRIPT",
                "message": "자막을 찾을 수 없습니다",
                "details": "이 영상은 자막이 제공되지 않습니다"
            }
        }