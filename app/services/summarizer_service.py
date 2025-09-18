"""
AI 요약 서비스 모듈
OpenAI GPT-5.0을 사용한 텍스트 요약 생성
"""
import os
from typing import Optional
from openai import OpenAI
from app.models.summary import Summary
from app.utils.logger import LoggerMixin, setup_logger


class SummarizerService(LoggerMixin):
    """AI를 사용한 텍스트 요약 서비스 클래스"""
    
    def __init__(self):
        # OpenAI 클라이언트 초기화
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.log_error("❌ OPENAI_API_KEY 환경 변수 누락")
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5"  # GPT-5 모델 사용
        self.log_info(f"🤖 AI 요약 서비스 초기화 완료", data={"model": self.model})
    
    async def generate_summary(
        self, 
        transcript: str, 
        title: str, 
        language: Optional[str] = None
    ) -> Summary:
        """
        자막 텍스트를 바탕으로 요약을 생성합니다.
        
        Args:
            transcript: 자막 텍스트
            title: 영상 제목
            language: 자막 언어 코드
            
        Returns:
            Summary: 요약 정보 객체
        """
        self.log_info(f"📝 요약 생성 시작", data={
            "title": title,
            "language": language,
            "transcript_length": len(transcript)
        })
        
        # 자막 길이 로깅만 하고 제한하지 않음
        self.log_info(f"📊 자막 길이 확인", data={
            "transcript_length": len(transcript)
        })
        
        # 언어에 따른 프롬프트 설정
        is_korean = language and language.startswith('ko')
        
        # 요약 생성을 위한 시스템 프롬프트
        system_prompt = """당신은 유튜브 영상 내용을 요약하는 전문가입니다.
주어진 자막을 바탕으로 체계적이고 이해하기 쉬운 요약을 작성해주세요.
한국어로 답변하세요."""
        
        # 사용자 프롬프트 구성
        user_prompt = f"""다음 유튜브 영상의 자막을 요약해주세요.

영상 제목: {title}
자막 언어: {language or '알 수 없음'}

자막 내용:
{transcript}

다음 형식으로 요약해주세요:

1. 한 줄 요약 (50자 이내):
[영상의 핵심 내용을 한 문장으로]

2. 핵심 포인트 (3-5개):
- [첫 번째 핵심 내용]
- [두 번째 핵심 내용]
- [세 번째 핵심 내용]

3. 상세 요약 (500자 이내):
[영상의 전체적인 내용과 맥락을 포함한 상세 요약]"""
        
        try:
            # OpenAI API 호출 (CLAUDE.md에서 제공한 코드 형식 사용)
            self.log_info("🤖 OpenAI GPT-5.0 API 호출 시작")
            
            # 전체 프롬프트 로깅
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            self.log_debug("📤 API 요청 데이터", data={
                "model": self.model,
                "prompt_length": len(full_prompt),
                "prompt": full_prompt  # 전문 로깅
            })
            
            # GPT-5 API 사용 (CLAUDE.md 형식)
            # OpenAI 라이브러리 1.107.3 버전에서 responses 메소드 지원
            response = self.client.responses.create(
                model=self.model,  # gpt-5
                input=full_prompt,
                reasoning={"effort": "medium"},  # 중간 수준의 추론
                text={"verbosity": "medium"}  # 중간 수준의 상세도
            )

            # 응답 텍스트 추출 (GPT-5 형식)
            output_text = response.output_text
            
            # API 응답 로깅 (전문)
            self.log_debug("📥 API 응답 수신", data={
                "response_length": len(output_text),
                "response_text": output_text  # 전문 로깅
            })
            
            # 응답을 파싱하여 Summary 객체 생성
            self.log_info("🔍 요약 응답 파싱 시작")
            summary = self._parse_summary_response(output_text)
            
            self.log_info(f"✅ 요약 생성 성공", data={
                "brief_length": len(summary.brief),
                "key_points_count": len(summary.key_points),
                "detailed_length": len(summary.detailed)
            })
            
            return summary
            
        except Exception as e:
            self.log_error(f"❌ OpenAI API 오류", data={
                "error": str(e),
                "title": title,
                "language": language
            })
            # 오류 발생 시 예외를 그대로 전파
            raise Exception(f"AI 요약 생성 실패: {str(e)}")
    
    def _parse_summary_response(self, response_text: str) -> Summary:
        """
        AI 응답을 파싱하여 Summary 객체를 생성합니다.
        
        Args:
            response_text: AI의 응답 텍스트
            
        Returns:
            Summary: 파싱된 요약 객체
        """
        self.log_debug("🔧 요약 파싱 시작", data={"response_length": len(response_text)})
        
        lines = response_text.strip().split('\n')
        
        # 기본값 설정
        brief = "요약을 생성할 수 없습니다."
        key_points = []
        detailed = ""
        
        # 섹션별로 파싱
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # 섹션 감지
            if "한 줄 요약" in line:
                current_section = "brief"
                continue
            elif "핵심 포인트" in line:
                current_section = "key_points"
                continue
            elif "상세 요약" in line:
                current_section = "detailed"
                continue
            
            # 내용 추출
            if current_section == "brief":
                # [로 시작하는 경우 대괄호 제거
                if line.startswith('[') and line.endswith(']'):
                    brief = line[1:-1]
                # 기본값이 아닌 실제 요약이 있으면 덮어쓰기
                elif line and not line.startswith("1.") and not line.startswith("2.") and not line.startswith("3."):
                    brief = line
            
            elif current_section == "key_points":
                # - 로 시작하는 항목 추출
                if line.startswith('-') or line.startswith('•'):
                    point = line[1:].strip()
                    if point:
                        key_points.append(point)
            
            elif current_section == "detailed":
                # [로 시작하는 경우 대괄호 제거
                if line.startswith('[') and line.endswith(']'):
                    detailed += line[1:-1] + " "
                else:
                    detailed += line + " "
        
        # 파싱 실패 시 에러
        if not key_points:
            self.log_error("❌ 핵심 포인트 파싱 실패", data={"parsed_data": {"brief": brief, "detailed": detailed}})
            raise ValueError("AI 응답에서 핵심 포인트를 추출할 수 없습니다")
        
        if not detailed:
            self.log_error("❌ 상세 요약 파싱 실패", data={"parsed_data": {"brief": brief, "key_points": key_points}})
            raise ValueError("AI 응답에서 상세 요약을 추출할 수 없습니다")
        
        result = Summary(
            brief=brief[:100],  # 최대 100자
            key_points=key_points[:5],  # 최대 5개
            detailed=detailed.strip()[:1000]  # 최대 1000자
        )
        
        self.log_debug("📦 파싱 결과", data={
            "brief": result.brief,
            "key_points": result.key_points,
            "detailed": result.detailed  # 전문 로깅
        })
        
        return result
    
