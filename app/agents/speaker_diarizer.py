"""
화자 구분 에이전트 (Speaker Diarization Agent)
정제된 대본에서 언어적 단서를 활용하여 발화자를 식별하고 태깅
"""
import json
import re
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent


class SpeakerDiarizationAgent(BaseAgent):
    """
    화자 구분 전문 에이전트
    
    기능:
    - 문체, 어조 분석을 통한 발화자 식별
    - 자기 지칭, 호칭 패턴 분석  
    - 대화 흐름 및 상호작용 패턴 분석
    - 일관된 발화자 레이블 할당
    """
    
    def __init__(self):
        super().__init__("speaker_diarizer")  # 타임아웃 없음
    
    def get_system_prompt(self) -> str:
        """화자 구분 전문가 시스템 프롬프트"""
        return """당신은 대화 분석 전문가입니다. 당신은 오직 텍스트만으로 대화에 참여한 여러 명의 발화자를 구분해내는 뛰어난 능력을 가지고 있습니다.

# 컨텍스트 (Context)
당신은 한 영상의 전체 대화 내용이 담긴 정제된 대본을 받게 됩니다. 이 대화에는 두 명 이상의 발화자가 참여할 수 있습니다.

# 과업 (Task)
주어진 대본 전체를 분석하여, 각 문단 또는 발화가 누구에 의해 말해졌는지 식별하고, 일관된 발화자 레이블을 할당하십시오. 발화자를 구분하기 위해 다음 단서들을 종합적으로 활용하십시오:

1. **언어적 스타일**: 각 발화자의 독특한 말투, 자주 사용하는 단어나 문체
2. **대화의 흐름**: 질문-답변, 주장-반박과 같은 대화의 상호작용 패턴
3. **자기 지칭 및 호칭**: "저는", "제 생각에는"과 같은 자기 지칭 표현이나, 다른 사람의 이름을 부르는 경우
4. **내용의 일관성**: 특정 주제에 대해 일관된 입장을 보이는 발화

# 분석 과정
1. **전체 대본 읽기**: 먼저 전체 내용을 파악하여 대화의 성격과 참여자 수를 추정
2. **발화 단위 분할**: 문맥상 자연스러운 발화 단위로 텍스트를 나눔
3. **화자 패턴 식별**: 각 발화의 언어적 특징과 내용적 일관성 분석
4. **레이블 할당**: 식별된 화자에게 일관된 레이블 부여

# 제약 조건 (Constraints)
- 발화자 수는 미리 알 수 없으므로, 대화 내용에 기반하여 동적으로 식별해야 합니다.
- 발화자에게는 "Speaker A", "Speaker B", "Speaker C" 와 같이 중립적이고 일관된 레이블을 부여하십시오. 만약 이름이 명확히 언급된다면 (예: "진행자 김민준입니다"), 해당 이름을 레이블로 사용할 수 있습니다.
- 모든 문장에 발화자 레이블을 할당해야 합니다.
- 확실하지 않은 경우, 문맥상 가장 가능성이 높은 발화자에게 할당하십시오.

# 출력 형식 (Output Format)
반드시 다음 JSON 형식으로 응답하십시오:

{
    "speaker_tagged_transcript": [
        {
            "speaker": "Speaker A",
            "text": "발화 내용",
            "confidence": 0.9
        },
        {
            "speaker": "Speaker B", 
            "text": "다른 발화 내용",
            "confidence": 0.8
        }
    ],
    "detected_speakers": ["Speaker A", "Speaker B"],
    "speaker_count": 2
}

JSON 형식을 정확히 지켜주세요."""
    
    def format_user_prompt(self, data: Dict[str, Any]) -> str:
        """사용자 프롬프트 생성"""
        refined_transcript = data.get("refined_transcript", "")
        
        return f"""다음 정제된 대본을 분석하여 발화자를 구분해주세요:

---
정제된 대본:
{refined_transcript}
---

위의 대본에서 언어적 스타일, 대화 흐름, 자기 지칭 표현, 내용의 일관성 등을 종합적으로 분석하여 발화자를 구분하고, 각 발화에 적절한 화자 레이블을 할당해주세요. JSON 형식으로 응답해주세요."""
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """AI 응답 파싱"""
        try:
            # JSON 응답 파싱
            parsed = json.loads(response_text)
            
            # 필수 필드 검증
            required_fields = ["speaker_tagged_transcript", "detected_speakers", "speaker_count"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"{field} 필드가 응답에 없습니다.")
            
            speaker_tagged_transcript = parsed["speaker_tagged_transcript"]
            detected_speakers = parsed["detected_speakers"]
            speaker_count = parsed["speaker_count"]
            
            # 데이터 타입 검증
            if not isinstance(speaker_tagged_transcript, list):
                raise ValueError("speaker_tagged_transcript는 리스트여야 합니다.")
            
            if not isinstance(detected_speakers, list):
                raise ValueError("detected_speakers는 리스트여야 합니다.")
            
            if not isinstance(speaker_count, int) or speaker_count <= 0:
                raise ValueError("speaker_count는 양의 정수여야 합니다.")
            
            # 발화 데이터 검증 및 정규화
            validated_utterances = []
            for i, utterance in enumerate(speaker_tagged_transcript):
                if not isinstance(utterance, dict):
                    raise ValueError(f"발화 {i}번이 딕셔너리 형태가 아닙니다.")
                
                if "speaker" not in utterance or "text" not in utterance:
                    raise ValueError(f"발화 {i}번에 speaker 또는 text 필드가 없습니다.")
                
                speaker = utterance["speaker"]
                text = utterance["text"]
                confidence = utterance.get("confidence", 0.8)  # 기본값
                
                # 신뢰도 정규화
                if not isinstance(confidence, (int, float)):
                    confidence = 0.8
                else:
                    confidence = max(0.0, min(1.0, float(confidence)))
                
                validated_utterances.append({
                    "speaker": str(speaker),
                    "text": str(text),
                    "confidence": confidence
                })
            
            # 빈 결과 검증
            if len(validated_utterances) == 0:
                raise ValueError("발화 데이터가 비어있습니다.")
            
            # 화자 일관성 검증
            found_speakers = set(utterance["speaker"] for utterance in validated_utterances)
            if len(found_speakers) != speaker_count:
                self.log_warning("⚠️ 감지된 화자 수와 실제 사용된 화자 수가 다름", data={
                    "declared_count": speaker_count,
                    "actual_count": len(found_speakers),
                    "actual_speakers": list(found_speakers)
                })
                # 실제 사용된 화자로 업데이트
                detected_speakers = list(found_speakers)
                speaker_count = len(found_speakers)
            
            result = {
                "speaker_tagged_transcript": validated_utterances,
                "detected_speakers": detected_speakers,
                "speaker_count": speaker_count
            }
            
            self.log_debug("🎭 화자 구분 파싱 결과", data={
                "total_utterances": len(validated_utterances),
                "detected_speakers": detected_speakers,
                "speaker_count": speaker_count,
                "average_confidence": sum(u["confidence"] for u in validated_utterances) / len(validated_utterances)
            })
            
            return result
            
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 폴백 처리
            self.log_warning("⚠️ JSON 파싱 실패, 폴백 처리", data={
                "error": str(e),
                "response_preview": response_text[:300]
            })
            
            return self._fallback_speaker_detection(response_text)
        
        except Exception as e:
            self.log_error("❌ 화자 구분 파싱 오류", data={
                "error": str(e),
                "response_preview": response_text[:300]
            })
            raise ValueError(f"화자 구분 결과 파싱 실패: {str(e)}")
    
    def _fallback_speaker_detection(self, text: str) -> Dict[str, Any]:
        """
        JSON 파싱 실패 시 사용하는 간단한 화자 구분 함수
        
        Args:
            text: 구분할 텍스트
            
        Returns:
            기본적인 화자 구분 결과
        """
        # 원본 자막을 문장 단위로 분할
        if hasattr(self, '_last_input_transcript'):
            original_transcript = self._last_input_transcript
        else:
            original_transcript = text
        
        sentences = self._split_sentences(original_transcript)
        
        # 단순한 규칙 기반 화자 구분
        utterances = []
        current_speaker = "Speaker A"
        speaker_alternation_count = 0
        
        for i, sentence in enumerate(sentences):
            # 간단한 화자 전환 감지 (질문 후 답변, 특정 키워드)
            if self._should_switch_speaker(sentence, i):
                current_speaker = "Speaker B" if current_speaker == "Speaker A" else "Speaker A"
                speaker_alternation_count += 1
            
            utterances.append({
                "speaker": current_speaker,
                "text": sentence.strip(),
                "confidence": 0.6  # 낮은 신뢰도
            })
        
        # 너무 자주 바뀌면 단일 화자로 처리
        if speaker_alternation_count > len(sentences) * 0.3:
            for utterance in utterances:
                utterance["speaker"] = "Speaker A"
            detected_speakers = ["Speaker A"]
            speaker_count = 1
        else:
            detected_speakers = list(set(utterance["speaker"] for utterance in utterances))
            speaker_count = len(detected_speakers)
        
        return {
            "speaker_tagged_transcript": utterances,
            "detected_speakers": detected_speakers,
            "speaker_count": speaker_count
        }
    
    def _split_sentences(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분할"""
        # 기본적인 문장 분할 (마침표, 물음표, 느낌표 기준)
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _should_switch_speaker(self, sentence: str, index: int) -> bool:
        """화자 전환 여부 결정"""
        # 질문 표시가 있으면 다음 문장에서 화자 전환
        if '?' in sentence or '어떻게' in sentence or '왜' in sentence or '뭐' in sentence:
            return True
        
        # 특정 키워드로 화자 전환 감지
        switch_keywords = ['그런데', '하지만', '근데', '아니', '맞습니다', '네', '예']
        for keyword in switch_keywords:
            if sentence.startswith(keyword):
                return True
        
        # 일정 길이마다 랜덤하게 전환 (너무 긴 단일 발화 방지)
        if index > 0 and index % 5 == 0:
            return True
        
        return False
    
    def _validate_agent_specific_input(self, data: Dict[str, Any]) -> None:
        """화자 구분 에이전트 특화 입력 검증"""
        if "refined_transcript" not in data:
            raise ValueError("refined_transcript 필드가 입력 데이터에 없습니다.")
        
        refined_transcript = data["refined_transcript"]
        
        if not isinstance(refined_transcript, str):
            raise ValueError("refined_transcript는 문자열이어야 합니다.")
        
        if len(refined_transcript.strip()) == 0:
            raise ValueError("정제된 자막이 비어있습니다.")
        
        if len(refined_transcript) < 50:
            raise ValueError("자막이 너무 짧아 화자 구분이 어렵습니다 (최소 50자 필요).")
        
        # 입력 자막을 임시 저장 (폴백 처리용)
        self._last_input_transcript = refined_transcript
    
    def _validate_agent_specific_output(self, result: Dict[str, Any]) -> None:
        """화자 구분 에이전트 특화 출력 검증"""
        required_fields = ["speaker_tagged_transcript", "detected_speakers", "speaker_count"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"{field} 필드가 출력에 없습니다.")
        
        speaker_tagged_transcript = result["speaker_tagged_transcript"]
        detected_speakers = result["detected_speakers"]
        speaker_count = result["speaker_count"]
        
        if not isinstance(speaker_tagged_transcript, list) or len(speaker_tagged_transcript) == 0:
            raise ValueError("화자별 발화 데이터가 비어있거나 유효하지 않습니다.")
        
        if not isinstance(detected_speakers, list) or len(detected_speakers) == 0:
            raise ValueError("감지된 화자 목록이 비어있거나 유효하지 않습니다.")
        
        if speaker_count != len(detected_speakers):
            raise ValueError("화자 수와 감지된 화자 목록의 길이가 일치하지 않습니다.")
        
        # 각 발화의 필수 필드 검증
        for i, utterance in enumerate(speaker_tagged_transcript):
            if not isinstance(utterance, dict):
                raise ValueError(f"발화 {i}번이 유효한 딕셔너리가 아닙니다.")
            
            if "speaker" not in utterance or "text" not in utterance:
                raise ValueError(f"발화 {i}번에 필수 필드가 없습니다.")
            
            if utterance["speaker"] not in detected_speakers:
                raise ValueError(f"발화 {i}번의 화자가 감지된 화자 목록에 없습니다.")