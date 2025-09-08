"""
멀티에이전트 오케스트레이터 서비스
여러 전문 AI 에이전트의 작업을 조율하는 마스터 서비스
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.utils.logger import LoggerMixin
from app.models.agent_models import (
    MultiAgentResult, 
    MultiAgentProcessingStatus,
    TranscriptRefinementInput,
    SpeakerDiarizationInput,
    TopicCohesionInput,
    StructureDesignInput,
    ReportSynthesisInput
)


class MultiAgentService(LoggerMixin):
    """
    멀티에이전트 시스템 오케스트레이터
    
    역할:
    1. 전체 워크플로우 관리
    2. 에이전트 간 데이터 전달
    3. 에러 처리 및 복구
    4. 진행 상태 추적
    5. 최종 결과물 취합
    """
    
    def __init__(self):
        """오케스트레이터 초기화"""
        self.agent_pipeline = [
            "transcript_refiner",
            "speaker_diarizer", 
            "topic_cohesion",
            "structure_designer",
            "report_synthesizer"
        ]
        
        # 에이전트 인스턴스들은 지연 초기화 (circular import 방지)
        self._agents = {}
        
        self.log_info("🎭 멀티에이전트 오케스트레이터 초기화 완료", data={
            "pipeline": self.agent_pipeline,
            "total_agents": len(self.agent_pipeline)
        })
    
    def _get_agent(self, agent_name: str):
        """
        에이전트 인스턴스 가져오기 (지연 초기화)
        
        Args:
            agent_name: 에이전트 명
            
        Returns:
            에이전트 인스턴스
        """
        if agent_name not in self._agents:
            # 지연 import로 circular dependency 방지
            if agent_name == "transcript_refiner":
                from app.agents.transcript_refiner import TranscriptRefinerAgent
                self._agents[agent_name] = TranscriptRefinerAgent()
            elif agent_name == "speaker_diarizer":
                from app.agents.speaker_diarizer import SpeakerDiarizationAgent
                self._agents[agent_name] = SpeakerDiarizationAgent()
            elif agent_name == "topic_cohesion":
                from app.agents.topic_cohesion import TopicCohesionAgent
                self._agents[agent_name] = TopicCohesionAgent()
            elif agent_name == "structure_designer":
                from app.agents.structure_designer import StructureDesignerAgent
                self._agents[agent_name] = StructureDesignerAgent()
            elif agent_name == "report_synthesizer":
                from app.agents.report_synthesizer import ReportSynthesizerAgent
                self._agents[agent_name] = ReportSynthesizerAgent()
            else:
                raise ValueError(f"알 수 없는 에이전트: {agent_name}")
        
        return self._agents[agent_name]
    
    async def process_full_analysis(
        self, 
        transcript: str,
        title: str,
        video_id: str,
        language: Optional[str] = None
    ) -> MultiAgentResult:
        """
        전체 멀티에이전트 분석 파이프라인 실행
        
        Args:
            transcript: 원본 자막 텍스트
            title: 영상 제목
            video_id: 비디오 ID
            language: 자막 언어
            
        Returns:
            전체 분석 결과
        """
        start_time = datetime.now()
        
        # 초기 상태 설정
        status = MultiAgentProcessingStatus(
            status="processing",
            started_at=start_time,
            completed_agents=[]
        )
        
        result = MultiAgentResult(processing_status=status)
        
        self.log_info("🚀 멀티에이전트 분석 시작", data={
            "video_id": video_id,
            "title": title,
            "language": language,
            "transcript_length": len(transcript),
            "pipeline": self.agent_pipeline
        })
        
        try:
            # 1단계: 자막 정제
            await self._update_status(result, "transcript_refiner")
            transcript_input = TranscriptRefinementInput(transcript=transcript)
            
            transcript_agent = self._get_agent("transcript_refiner")
            transcript_result = await transcript_agent.process(transcript_input.model_dump())
            result.transcript_refinement = transcript_result
            await self._mark_completed(result, "transcript_refiner")
            
            # 2단계: 화자 구분
            await self._update_status(result, "speaker_diarizer")
            speaker_input = SpeakerDiarizationInput(
                refined_transcript=transcript_result.get("refined_transcript")
            )
            
            speaker_agent = self._get_agent("speaker_diarizer")
            speaker_result = await speaker_agent.process(speaker_input.model_dump())
            result.speaker_diarization = speaker_result
            await self._mark_completed(result, "speaker_diarizer")
            
            # 3단계: 주제 응집
            await self._update_status(result, "topic_cohesion")
            topic_input = TopicCohesionInput(
                speaker_tagged_transcript=speaker_result.get("speaker_tagged_transcript", [])
            )
            
            topic_agent = self._get_agent("topic_cohesion")
            topic_result = await topic_agent.process(topic_input.model_dump())
            result.topic_cohesion = topic_result
            await self._mark_completed(result, "topic_cohesion")
            
            # 4단계: 구조 설계
            await self._update_status(result, "structure_designer")
            structure_input = StructureDesignInput(
                topic_clusters=topic_result.get("topic_clusters", [])
            )
            
            structure_agent = self._get_agent("structure_designer")
            structure_result = await structure_agent.process(structure_input.model_dump())
            result.structure_design = structure_result
            await self._mark_completed(result, "structure_designer")
            
            # 5단계: 보고서 종합
            await self._update_status(result, "report_synthesizer")
            synthesis_input = ReportSynthesisInput(
                topic_clusters=topic_result.get("topic_clusters", []),
                report_structure=structure_result.get("report_structure", []),
                content_type=structure_result.get("content_type", "일반")
            )
            
            synthesis_agent = self._get_agent("report_synthesizer")
            synthesis_result = await synthesis_agent.process(synthesis_input.model_dump())
            result.report_synthesis = synthesis_result
            await self._mark_completed(result, "report_synthesizer")
            
            # 완료 처리
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result.processing_status.status = "completed"
            result.processing_status.completed_at = end_time
            result.processing_status.total_processing_time = processing_time
            result.processing_status.current_agent = None
            result.successful_agents = len(result.processing_status.completed_agents)
            
            self.log_info("✅ 멀티에이전트 분석 완료", data={
                "video_id": video_id,
                "total_time": f"{processing_time:.2f}초",
                "successful_agents": result.successful_agents,
                "completed_agents": result.processing_status.completed_agents
            })
            
            return result
            
        except Exception as e:
            # 실패 처리
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result.processing_status.status = "failed"
            result.processing_status.error_message = str(e)
            result.processing_status.completed_at = end_time
            result.processing_status.total_processing_time = processing_time
            result.successful_agents = len(result.processing_status.completed_agents)
            
            self.log_error("❌ 멀티에이전트 분석 실패", data={
                "video_id": video_id,
                "error": str(e),
                "current_agent": result.processing_status.current_agent,
                "completed_agents": result.processing_status.completed_agents,
                "elapsed_time": f"{processing_time:.2f}초"
            })
            
            # 부분 성공도 유효한 결과로 반환 (디버깅 및 개선 목적)
            return result
    
    async def _update_status(self, result: MultiAgentResult, current_agent: str) -> None:
        """
        처리 상태 업데이트
        
        Args:
            result: 현재 결과 객체
            current_agent: 현재 처리 중인 에이전트명
        """
        result.processing_status.current_agent = current_agent
        
        self.log_info(f"🔄 에이전트 처리 시작: {current_agent}", data={
            "current_agent": current_agent,
            "completed_agents": result.processing_status.completed_agents,
            "remaining": [a for a in self.agent_pipeline if a not in result.processing_status.completed_agents]
        })
    
    async def _mark_completed(self, result: MultiAgentResult, agent_name: str) -> None:
        """
        에이전트 완료 처리
        
        Args:
            result: 현재 결과 객체
            agent_name: 완료된 에이전트명
        """
        if agent_name not in result.processing_status.completed_agents:
            result.processing_status.completed_agents.append(agent_name)
        
        self.log_info(f"✅ 에이전트 처리 완료: {agent_name}", data={
            "completed_agent": agent_name,
            "total_completed": len(result.processing_status.completed_agents),
            "total_agents": len(self.agent_pipeline),
            "progress": f"{len(result.processing_status.completed_agents)}/{len(self.agent_pipeline)}"
        })
    
    async def get_processing_status(self, result: MultiAgentResult) -> Dict[str, Any]:
        """
        현재 처리 상태 반환
        
        Args:
            result: 결과 객체
            
        Returns:
            상태 정보 딕셔너리
        """
        status_info = {
            "status": result.processing_status.status,
            "current_agent": result.processing_status.current_agent,
            "progress": {
                "completed": len(result.processing_status.completed_agents),
                "total": len(self.agent_pipeline),
                "percentage": round((len(result.processing_status.completed_agents) / len(self.agent_pipeline)) * 100, 1)
            },
            "completed_agents": result.processing_status.completed_agents,
            "remaining_agents": [
                agent for agent in self.agent_pipeline 
                if agent not in result.processing_status.completed_agents
            ],
            "processing_time": result.processing_status.total_processing_time,
            "error_message": result.processing_status.error_message
        }
        
        return status_info
    
    def validate_pipeline_integrity(self) -> bool:
        """
        파이프라인 무결성 검증
        모든 에이전트가 올바르게 로드될 수 있는지 확인
        
        Returns:
            검증 성공 여부
        """
        try:
            self.log_info("🔍 파이프라인 무결성 검증 시작")
            
            for agent_name in self.agent_pipeline:
                agent = self._get_agent(agent_name)
                if not hasattr(agent, 'process'):
                    raise ValueError(f"{agent_name} 에이전트가 process 메서드를 구현하지 않았습니다.")
            
            self.log_info("✅ 파이프라인 무결성 검증 성공", data={
                "validated_agents": self.agent_pipeline
            })
            return True
            
        except Exception as e:
            self.log_error("❌ 파이프라인 무결성 검증 실패", data={
                "error": str(e)
            })
            return False