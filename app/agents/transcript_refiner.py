"""
자막 정제 에이전트 (Transcript Refinement Agent)
ASR 오류가 포함된 원본 자막을 깨끗하고 가독성 높은 텍스트로 정제
"""
import re
import json
from typing import Dict, Any
from app.agents.base_agent import BaseAgent


class TranscriptRefinerAgent(BaseAgent):
    """
    자막 정제 전문 에이전트
    
    기능:
    - 오탈자 및 문법 오류 수정
    - 구두점 추가 및 정리
    - 간투사 및 반복어 제거
    - 원본 의미 보존 최우선
    """
    
    def __init__(self):
        super().__init__("transcript_refiner")  # 타임아웃 없음
    
    def get_system_prompt(self) -> str:
        """자막 정제 전문가 시스템 프롬프트"""
        return """당신은 전문적인 교정 및 교열 전문가입니다. 당신의 임무는 자동 음성 인식(ASR)을 통해 생성된 자막 텍스트를 사람이 작성한 것처럼 자연스럽고 문법적으로 완벽한 문장으로 다듬는 것입니다.

# 컨텍스트 (Context)
당신은 영상의 전체 자막 텍스트를 받게 됩니다. 이 텍스트는 오탈자, 문법 오류, 구두점 누락, 그리고 "음", "어", "그니까" 와 같은 불필요한 간투사를 포함하고 있을 수 있습니다.

# 과업 (Task)
주어진 자막 텍스트 전체에 대해 다음 작업을 수행하여 정제된 최종 대본을 생성하십시오:

1. **오탈자 및 문법 오류 수정**: 문맥을 파악하여 명백한 오탈자와 문법적 오류를 수정하십시오.
2. **구두점 추가**: 문장의 의미와 흐름에 맞게 마침표(.), 쉼표(,), 물음표(?) 등을 정확하게 추가하여 가독성을 높이십시오.
3. **간투사 및 반복어 제거**: 대화의 흐름을 방해하는 불필요한 간투사나 의미 없는 반복어를 제거하되, 발화의 의도가 왜곡되지 않도록 주의하십시오.

# 제약 조건 (Constraints)
- **정보 보존의 원칙**: 어떤 경우에도 원본의 핵심 의미, 사실 관계, 고유명사, 전문 용어를 변경하거나 삭제해서는 안 됩니다. 당신의 역할은 '정제'이지 '요약'이 아닙니다.
- **객관성 유지**: 당신의 개인적인 의견이나 해석을 추가하지 마십시오. 오직 주어진 텍스트의 표현을 명확하게 만드는 데에만 집중하십시오.

# 출력 형식 (Output Format)
반드시 다음 JSON 형식으로 응답하십시오:

{
    "refined_transcript": "정제된 자막 텍스트 전문",
    "processing_notes": "처리 과정에서의 주요 수정사항이나 특이사항 (선택적)"
}

JSON 형식을 정확히 지켜주세요."""
    
    def format_user_prompt(self, data: Dict[str, Any]) -> str:
        """사용자 프롬프트 생성"""
        transcript = data.get("transcript", "")
        
        return f"""다음 자막 텍스트를 정제해주세요:

---
원본 자막:
{transcript}
---

위의 자막을 오탈자 수정, 구두점 추가, 간투사 제거 등을 통해 깔끔하게 정제하되, 원본의 의미와 내용을 절대 변경하지 마십시오. JSON 형식으로 응답해주세요."""
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """AI 응답 파싱"""
        try:
            # JSON 응답 파싱 시도
            parsed = json.loads(response_text)
            
            # 필수 필드 검증
            if "refined_transcript" not in parsed:
                raise ValueError("refined_transcript 필드가 응답에 없습니다.")
            
            refined_transcript = parsed["refined_transcript"]
            processing_notes = parsed.get("processing_notes", "정제 완료")
            
            # 빈 결과 검증
            if not refined_transcript or len(refined_transcript.strip()) == 0:
                raise ValueError("정제된 자막이 비어있습니다.")
            
            result = {
                "refined_transcript": refined_transcript.strip(),
                "processing_notes": processing_notes
            }
            
            self.log_debug("📝 자막 정제 파싱 결과", data={
                "original_length": len(self._last_input_transcript) if hasattr(self, '_last_input_transcript') else 0,
                "refined_length": len(refined_transcript),
                "processing_notes": processing_notes
            })
            
            return result
            
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 텍스트 직접 사용 (폴백)
            self.log_warning("⚠️ JSON 파싱 실패, 원본 텍스트 사용", data={
                "error": str(e),
                "response_preview": response_text[:200]
            })
            
            # 간단한 정제 시도
            cleaned_text = self._fallback_text_cleaning(response_text)
            
            return {
                "refined_transcript": cleaned_text,
                "processing_notes": "JSON 파싱 실패로 인한 폴백 처리"
            }
        
        except Exception as e:
            self.log_error("❌ 자막 정제 파싱 오류", data={
                "error": str(e),
                "response_preview": response_text[:200]
            })
            raise ValueError(f"자막 정제 결과 파싱 실패: {str(e)}")
    
    def _fallback_text_cleaning(self, text: str) -> str:
        """
        JSON 파싱 실패 시 사용하는 간단한 텍스트 정제 함수
        
        Args:
            text: 정제할 텍스트
            
        Returns:
            기본적으로 정제된 텍스트
        """
        # JSON 관련 문자 제거
        text = re.sub(r'^\s*{\s*"refined_transcript"\s*:\s*"', '', text)
        text = re.sub(r'",?\s*"processing_notes".*}?\s*$', '', text)
        text = re.sub(r'^"|"$', '', text)  # 시작/끝 따옴표 제거
        
        # 기본적인 간투사 제거
        filler_words = ['음', '어', '아', '그니까', '뭐', '저기', '그', '이제', '막']
        for word in filler_words:
            text = re.sub(f'\\b{word}\\b\\s*', '', text)
        
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _validate_agent_specific_input(self, data: Dict[str, Any]) -> None:
        """자막 정제 에이전트 특화 입력 검증"""
        if "transcript" not in data:
            raise ValueError("transcript 필드가 입력 데이터에 없습니다.")
        
        transcript = data["transcript"]
        
        if not isinstance(transcript, str):
            raise ValueError("transcript는 문자열이어야 합니다.")
        
        if len(transcript.strip()) == 0:
            raise ValueError("자막 텍스트가 비어있습니다.")
        
        if len(transcript) < 10:
            raise ValueError("자막이 너무 짧습니다 (최소 10자 필요).")
        
        # 입력 자막을 임시 저장 (파싱 시 길이 비교용)
        self._last_input_transcript = transcript
    
    def _validate_agent_specific_output(self, result: Dict[str, Any]) -> None:
        """자막 정제 에이전트 특화 출력 검증"""
        if "refined_transcript" not in result:
            raise ValueError("refined_transcript 필드가 출력에 없습니다.")
        
        refined_transcript = result["refined_transcript"]
        
        if not isinstance(refined_transcript, str):
            raise ValueError("refined_transcript는 문자열이어야 합니다.")
        
        if len(refined_transcript.strip()) == 0:
            raise ValueError("정제된 자막이 비어있습니다.")
        
        # 원본과 비교하여 극단적인 길이 변화 검증
        if hasattr(self, '_last_input_transcript'):
            original_length = len(self._last_input_transcript)
            refined_length = len(refined_transcript)
            
            # 50% 이하로 줄어들거나 200% 이상 늘어나면 경고
            if refined_length < original_length * 0.5:
                self.log_warning("⚠️ 정제된 자막이 원본의 50% 이하로 줄어듦", data={
                    "original_length": original_length,
                    "refined_length": refined_length,
                    "reduction_ratio": refined_length / original_length
                })
            elif refined_length > original_length * 2.0:
                self.log_warning("⚠️ 정제된 자막이 원본의 200% 이상으로 늘어남", data={
                    "original_length": original_length,
                    "refined_length": refined_length,
                    "expansion_ratio": refined_length / original_length
                })