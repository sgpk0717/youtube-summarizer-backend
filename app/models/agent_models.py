"""
멀티에이전트 시스템용 데이터 모델
각 에이전트의 입출력 데이터 구조 정의
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# 에이전트 간 전달되는 데이터 모델

class TranscriptRefinementInput(BaseModel):
    """자막 정제 에이전트 입력 데이터"""
    transcript: str = Field(..., description="원본 자막 텍스트")


class TranscriptRefinementOutput(BaseModel):
    """자막 정제 에이전트 출력 데이터"""
    refined_transcript: str = Field(..., description="정제된 자막 텍스트")
    processing_notes: Optional[str] = Field(None, description="처리 과정 메모")


class SpeakerDiarizationInput(BaseModel):
    """화자 구분 에이전트 입력 데이터"""
    refined_transcript: str = Field(..., description="정제된 자막 텍스트")


class SpeakerUtterance(BaseModel):
    """개별 발화 데이터"""
    speaker: str = Field(..., description="발화자 식별자 (예: Speaker A)")
    text: str = Field(..., description="발화 내용")
    confidence: Optional[float] = Field(None, description="화자 구분 신뢰도 (0-1)")


class SpeakerDiarizationOutput(BaseModel):
    """화자 구분 에이전트 출력 데이터"""
    speaker_tagged_transcript: List[SpeakerUtterance] = Field(..., description="화자별로 태깅된 발화 리스트")
    detected_speakers: List[str] = Field(..., description="감지된 화자 목록")
    speaker_count: int = Field(..., description="감지된 화자 수")


class TopicCohesionInput(BaseModel):
    """주제 응집 에이전트 입력 데이터"""
    speaker_tagged_transcript: List[SpeakerUtterance] = Field(..., description="화자별 태깅된 발화")


class TopicCluster(BaseModel):
    """주제 클러스터 데이터"""
    topic_title: str = Field(..., description="주제 제목")
    related_utterances: List[SpeakerUtterance] = Field(..., description="해당 주제와 관련된 모든 발화")
    topic_summary: Optional[str] = Field(None, description="주제별 간단 요약")
    importance_score: Optional[float] = Field(None, description="주제 중요도 점수 (0-1)")


class TopicCohesionOutput(BaseModel):
    """주제 응집 에이전트 출력 데이터"""
    topic_clusters: List[TopicCluster] = Field(..., description="주제별로 그룹화된 클러스터")
    total_topics: int = Field(..., description="식별된 총 주제 수")


class StructureDesignInput(BaseModel):
    """보고서 구조 설계 에이전트 입력 데이터"""
    topic_clusters: List[TopicCluster] = Field(..., description="주제 클러스터")


class ReportSection(BaseModel):
    """보고서 섹션 정의"""
    section_name: str = Field(..., description="섹션명")
    section_description: str = Field(..., description="섹션 설명")
    required_topics: List[str] = Field(..., description="포함되어야 할 주제 제목들")
    section_order: int = Field(..., description="섹션 순서")


class StructureDesignOutput(BaseModel):
    """보고서 구조 설계 에이전트 출력 데이터"""
    content_type: str = Field(..., description="콘텐츠 유형 분석 결과 (예: 패널토론, 강의, 뉴스)")
    report_structure: List[ReportSection] = Field(..., description="보고서 구조 정의")
    structure_rationale: Optional[str] = Field(None, description="구조 결정 근거")


class ReportSynthesisInput(BaseModel):
    """보고서 종합 에이전트 입력 데이터"""
    topic_clusters: List[TopicCluster] = Field(..., description="주제 클러스터")
    report_structure: List[ReportSection] = Field(..., description="보고서 구조")
    content_type: str = Field(..., description="콘텐츠 유형")


class ReportSynthesisOutput(BaseModel):
    """보고서 종합 에이전트 출력 데이터"""
    final_report: str = Field(..., description="최종 종합 분석 보고서 (Markdown 형식)")
    report_metadata: Dict[str, Any] = Field(default_factory=dict, description="보고서 메타데이터")
    word_count: Optional[int] = Field(None, description="보고서 단어 수")


# ================================
# 멀티에이전트 처리 결과 모델
# ================================

class MultiAgentProcessingStatus(BaseModel):
    """멀티에이전트 처리 상태"""
    status: str = Field(..., description="처리 상태 (pending, processing, completed, failed)")
    current_agent: Optional[str] = Field(None, description="현재 처리 중인 에이전트")
    completed_agents: List[str] = Field(default_factory=list, description="완료된 에이전트 목록")
    error_message: Optional[str] = Field(None, description="에러 메시지 (실패 시)")
    started_at: Optional[datetime] = Field(None, description="처리 시작 시간")
    completed_at: Optional[datetime] = Field(None, description="처리 완료 시간")
    total_processing_time: Optional[float] = Field(None, description="총 처리 시간 (초)")


class MultiAgentResult(BaseModel):
    """멀티에이전트 시스템 최종 결과"""
    # 각 에이전트의 중간 결과
    transcript_refinement: Optional[TranscriptRefinementOutput] = Field(None, description="자막 정제 결과")
    speaker_diarization: Optional[SpeakerDiarizationOutput] = Field(None, description="화자 구분 결과") 
    topic_cohesion: Optional[TopicCohesionOutput] = Field(None, description="주제 응집 결과")
    structure_design: Optional[StructureDesignOutput] = Field(None, description="구조 설계 결과")
    report_synthesis: Optional[ReportSynthesisOutput] = Field(None, description="보고서 종합 결과")
    
    # 처리 상태 정보
    processing_status: MultiAgentProcessingStatus = Field(..., description="처리 상태 정보")
    
    # 전체 처리 통계
    total_agents: int = Field(default=5, description="총 에이전트 수")
    successful_agents: int = Field(default=0, description="성공한 에이전트 수")


# ================================
# API 요청/응답 모델
# ================================

class MultiAgentAnalyzeRequest(BaseModel):
    """멀티에이전트 분석 요청 모델"""
    url: str = Field(..., description="유튜브 영상 URL", example="https://youtube.com/watch?v=dQw4w9WgXcQ")
    enable_caching: bool = Field(default=True, description="캐싱 활성화 여부")
    detailed_logging: bool = Field(default=False, description="상세 로깅 활성화 여부")


class MultiAgentAnalyzeResponse(BaseModel):
    """멀티에이전트 분석 응답 모델"""
    # 기본 비디오 정보
    video_id: str = Field(..., description="유튜브 비디오 ID")
    title: str = Field(..., description="영상 제목")
    channel: str = Field(..., description="채널명")
    duration: str = Field(..., description="영상 길이")
    language: Optional[str] = Field(None, description="자막 언어 코드")
    
    # 멀티에이전트 분석 결과
    analysis_result: MultiAgentResult = Field(..., description="멀티에이전트 분석 결과")
    
    # 최종 보고서 (편의성을 위해 최상위에도 포함)
    final_report: Optional[str] = Field(None, description="최종 종합 분석 보고서")
    
    # 메타데이터
    transcript_available: bool = Field(..., description="자막 사용 가능 여부")
    analysis_type: str = Field(default="multi_agent", description="분석 유형")
    
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
                "analysis_type": "multi_agent"
            }
        }


# ================================
# 데이터베이스 저장용 모델
# ================================

class MultiAgentDatabaseRecord(BaseModel):
    """데이터베이스 저장용 멀티에이전트 결과"""
    video_id: str = Field(..., description="비디오 ID")
    analysis_result: Dict[str, Any] = Field(..., description="전체 분석 결과 (JSON 형태)")
    processing_status: str = Field(..., description="처리 상태")
    final_report: Optional[str] = Field(None, description="최종 보고서")
    processing_time: Optional[float] = Field(None, description="처리 시간")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.now, description="수정 시간")