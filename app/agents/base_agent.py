"""
베이스 에이전트 클래스
모든 전문 에이전트들이 상속받는 추상 베이스 클래스
"""
import os
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from openai import OpenAI
from app.utils.logger import LoggerMixin


class BaseAgent(LoggerMixin, ABC):
    """
    모든 멀티에이전트가 상속받는 베이스 클래스
    
    공통 기능:
    - OpenAI API 클라이언트 관리
    - 구조화된 로깅
    - 에러 처리 및 재시도 로직
    - 타임아웃 없음 (긴 영상 처리 지원)
    """
    
    def __init__(self, agent_name: str):
        """
        베이스 에이전트 초기화

        Args:
            agent_name: 에이전트 식별명 (로깅용)
        """
        self.agent_name = agent_name
        self.timeout = None  # 타임아웃 제거 - 긴 영상 처리를 위함

        # OpenAI 클라이언트 초기화
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.log_error("❌ OPENAI_API_KEY 환경 변수 누락")
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        self.openai_client = OpenAI(api_key=api_key)
        # 환경변수에서 모델명 읽기 (기본값: gpt-5)
        self.model = os.getenv("LLM_MODEL", "gpt-5")

        self.log_info(f"🤖 {self.agent_name} 에이전트 초기화 완료", data={
            "agent_name": self.agent_name,
            "model": self.model
        })
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        각 에이전트의 고유한 시스템 프롬프트 반환
        
        Returns:
            시스템 프롬프트 문자열
        """
        pass
    
    @abstractmethod
    def format_user_prompt(self, data: Dict[str, Any]) -> str:
        """
        입력 데이터를 기반으로 사용자 프롬프트 생성
        
        Args:
            data: 처리할 입력 데이터
            
        Returns:
            포맷된 사용자 프롬프트
        """
        pass
    
    @abstractmethod
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        AI 응답을 파싱하여 구조화된 데이터로 변환
        
        Args:
            response_text: AI의 응답 텍스트
            
        Returns:
            파싱된 결과 딕셔너리
        """
        pass
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        에이전트의 핵심 처리 메서드
        재시도, 에러 처리가 포함된 완전한 처리 파이프라인 (타임아웃 없음)
        
        Args:
            data: 처리할 입력 데이터
            
        Returns:
            처리 결과 딕셔너리
            
        Raises:
            ValueError: 입력 데이터 검증 실패
            Exception: 처리 중 예외 발생
        """
        start_time = asyncio.get_event_loop().time()
        
        self.log_info(f"🚀 {self.agent_name} 처리 시작", data={
            "input_keys": list(data.keys())
        })
        
        try:
            # 타임아웃 없음 - 긴 영상 처리 지원
            result = await self._process_with_retry(data)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            self.log_info(f"✅ {self.agent_name} 처리 완료", data={
                "processing_time": f"{processing_time:.2f}초",
                "output_keys": list(result.keys())
            })
            
            return result
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            self.log_error(f"❌ {self.agent_name} 처리 실패", data={
                "error": str(e),
                "error_type": type(e).__name__,
                "elapsed_time": f"{processing_time:.2f}초"
            })
            raise
    
    async def _process_with_retry(self, data: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        재시도 로직이 포함된 내부 처리 메서드
        
        Args:
            data: 처리할 입력 데이터
            max_retries: 최대 재시도 횟수
            
        Returns:
            처리 결과
        """
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.log_info(f"🔄 {self.agent_name} 재시도 {attempt}/{max_retries}")
                
                # 입력 데이터 검증
                self._validate_input(data)
                
                # AI API 호출
                result = await self._call_ai_api(data)
                
                # 결과 검증
                self._validate_output(result)
                
                return result
                
            except Exception as e:
                if attempt == max_retries:
                    # 마지막 시도에서도 실패하면 예외 전파
                    raise
                
                self.log_warning(f"⚠️ {self.agent_name} 시도 {attempt + 1} 실패, 재시도 중...", data={
                    "error": str(e),
                    "retry_in": 2 ** attempt  # 지수 백오프
                })
                
                # 지수 백오프로 대기
                await asyncio.sleep(2 ** attempt)
    
    async def _call_ai_api(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        OpenAI API 호출 및 응답 처리
        
        Args:
            data: 입력 데이터
            
        Returns:
            파싱된 AI 응답
        """
        system_prompt = self.get_system_prompt()
        user_prompt = self.format_user_prompt(data)
        
        self.log_debug(f"📤 {self.agent_name} API 호출", data={
            "system_prompt_length": len(system_prompt),
            "user_prompt_length": len(user_prompt),
            "model": self.model
        })
        
        # GPT-5 API 호출 (CLAUDE.md 형식)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.openai_client.responses.create(
            model=self.model,  # gpt-5
            input=full_prompt,
            reasoning={"effort": "medium"},  # 중간 수준의 추론
            text={"verbosity": "medium"}  # 중간 수준의 상세도
        )

        response_text = response.output_text
        
        self.log_debug(f"📥 {self.agent_name} API 응답 수신", data={
            "response_length": len(response_text)
        })
        
        # 응답 파싱
        parsed_result = self.parse_response(response_text)
        
        return parsed_result
    
    def _validate_input(self, data: Dict[str, Any]) -> None:
        """
        입력 데이터 유효성 검증
        
        Args:
            data: 검증할 입력 데이터
            
        Raises:
            ValueError: 입력 데이터가 유효하지 않을 때
        """
        if not isinstance(data, dict):
            raise ValueError("입력 데이터는 딕셔너리 형태여야 합니다.")
        
        if not data:
            raise ValueError("입력 데이터가 비어있습니다.")
        
        # 각 에이전트에서 오버라이드하여 특화된 검증 로직 구현
        self._validate_agent_specific_input(data)
    
    def _validate_agent_specific_input(self, data: Dict[str, Any]) -> None:
        """
        에이전트별 특화된 입력 검증 로직
        각 에이전트에서 필요에 따라 오버라이드
        
        Args:
            data: 검증할 입력 데이터
        """
        pass
    
    def _validate_output(self, result: Dict[str, Any]) -> None:
        """
        출력 데이터 유효성 검증
        
        Args:
            result: 검증할 출력 데이터
            
        Raises:
            ValueError: 출력 데이터가 유효하지 않을 때
        """
        if not isinstance(result, dict):
            raise ValueError("출력 데이터는 딕셔너리 형태여야 합니다.")
        
        if not result:
            raise ValueError("출력 데이터가 비어있습니다.")
        
        # 각 에이전트에서 오버라이드하여 특화된 검증 로직 구현
        self._validate_agent_specific_output(result)
    
    def _validate_agent_specific_output(self, result: Dict[str, Any]) -> None:
        """
        에이전트별 특화된 출력 검증 로직
        각 에이전트에서 필요에 따라 오버라이드
        
        Args:
            result: 검증할 출력 데이터
        """
        pass