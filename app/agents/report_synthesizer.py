"""
보고서 종합 에이전트 (Report Synthesis Agent)
주제 클러스터와 구조 설계를 바탕으로 최종 종합 분석 보고서 생성
"""
import json
import re
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent


class ReportSynthesizerAgent(BaseAgent):
    """
    보고서 종합 전문 에이전트
    
    기능:
    - 구조 설계도에 따른 체계적 보고서 작성
    - 주제별 내용 종합 및 재구성
    - 논리적 흐름과 가독성 최적화
    - Markdown 형식의 전문적 문서 생성
    """
    
    def __init__(self):
        super().__init__("report_synthesizer")  # 타임아웃 없음
    
    def get_system_prompt(self) -> str:
        """보고서 종합 전문가 시스템 프롬프트"""
        return """당신은 뛰어난 분석가이자 전문 작가입니다. 당신은 복잡한 데이터와 명확한 구조 설계도를 받아, 이를 바탕으로 매우 상세하고 논리 정연하며 가독성 높은 종합 보고서를 작성할 수 있습니다.

# 컨텍스트 (Context)
당신은 두 가지 핵심 자료를 받게 됩니다:
1. **콘텐츠 데이터**: 영상의 모든 내용이 주제별로 묶여있는 데이터
2. **구조 설계도**: 이 데이터를 어떤 구조로 풀어내야 하는지에 대한 명확한 가이드라인

# 과업 (Task)
주어진 '구조 설계도'를 청사진으로 삼아, '콘텐츠 데이터'의 모든 정보를 빠짐없이 사용하여 최종 종합 분석 보고서를 작성하십시오.

## 작성 원칙
1. **구조 충실성**: 설계도에 명시된 각 섹션과 하위 섹션을 순서대로 채워나가십시오.
2. **내용 완전성**: 각 섹션을 작성할 때는, 콘텐츠 데이터에서 해당 주제의 발화들을 가져와 내용을 종합하고 재구성하십시오.
3. **서술 전문성**: 단순한 발화 나열이 아닌, 논리적인 흐름을 가진 서술형 문장으로 작성해야 합니다.
4. **인용 활용**: 필요하다면 핵심적인 발언을 직접 인용하여 주장을 뒷받침할 수 있습니다.

## 작성 스타일
- **객관적 분석**: 사실과 발언 내용에 기반한 객관적 분석
- **논리적 구성**: 각 섹션이 자연스럽게 연결되는 논리적 흐름
- **전문적 문체**: 보고서에 적합한 격식있고 명확한 문체
- **가독성 최적화**: 제목, 소제목, 글머리 기호를 활용한 체계적 구성

## Markdown 형식 가이드
```markdown
# 제목 (H1)
## 주요 섹션 (H2)
### 하위 섹션 (H3)
- 글머리 기호
- **굵은 글씨**: 중요 내용 강조
- *기울임체*: 발언 인용 시 사용
- > 인용문: 중요한 발언 인용
```

# 제약 조건 (Constraints)
- **정보 무손실 원칙**: 콘텐츠 데이터에 있는 모든 정보는 최종 보고서에 어떤 형태로든 반드시 포함되어야 합니다. 내용을 임의로 요약하거나 생략하지 마십시오.
- **객관성 및 근거 기반 작성**: 당신의 개인적인 의견이나 데이터에 없는 정보를 추가하지 마십시오. 모든 서술은 주어진 콘텐츠 데이터에 근거해야 합니다.
- **구조 준수**: 제공된 구조 설계도를 반드시 따라야 하며, 섹션을 임의로 추가하거나 제거하지 마십시오.

# 출력 형식 (Output Format)
반드시 다음 JSON 형식으로 응답하십시오:

{
    "final_report": "# 종합 분석 보고서\\n\\n## 개요\\n...전체 보고서 내용 (Markdown 형식)",
    "report_metadata": {
        "total_sections": 4,
        "content_type": "패널토론",
        "topics_covered": ["주제1", "주제2", "주제3"],
        "word_count_estimate": 2500
    },
    "word_count": 2487
}

JSON 형식을 정확히 지켜주세요."""
    
    def format_user_prompt(self, data: Dict[str, Any]) -> str:
        """사용자 프롬프트 생성"""
        topic_clusters = data.get("topic_clusters", [])
        report_structure = data.get("report_structure", [])
        content_type = data.get("content_type", "일반")
        
        # 구조 설계도 포맷팅
        structure_guide = f"**콘텐츠 유형**: {content_type}\n\n"
        structure_guide += "**보고서 구조**:\n"
        
        for section in report_structure:
            section_name = section.get("section_name", "")
            section_description = section.get("section_description", "")
            required_topics = section.get("required_topics", [])
            section_order = section.get("section_order", 0)
            
            structure_guide += f"{section_order}. **{section_name}**\n"
            structure_guide += f"   - 설명: {section_description}\n"
            structure_guide += f"   - 포함할 주제: {', '.join(required_topics)}\n\n"
        
        # 주제별 콘텐츠 데이터 포맷팅
        content_data = ""
        for i, cluster in enumerate(topic_clusters):
            topic_title = cluster.get("topic_title", f"주제 {i+1}")
            topic_summary = cluster.get("topic_summary", "")
            importance_score = cluster.get("importance_score", 0.5)
            related_utterances = cluster.get("related_utterances", [])
            
            content_data += f"## 주제: {topic_title}\n"
            content_data += f"**요약**: {topic_summary}\n"
            content_data += f"**중요도**: {importance_score:.1f}\n"
            content_data += f"**관련 발화 ({len(related_utterances)}개)**:\n"
            
            for j, utterance in enumerate(related_utterances):
                speaker = utterance.get("speaker", "Unknown")
                text = utterance.get("text", "")
                confidence = utterance.get("confidence", 0.8)
                
                content_data += f"{j+1}. [{speaker}] (신뢰도: {confidence:.1f}): {text}\n"
            
            content_data += "\n"
        
        return f"""다음 구조 설계도와 콘텐츠 데이터를 바탕으로 종합 분석 보고서를 작성해주세요:

---
## 구조 설계도
{structure_guide}

## 콘텐츠 데이터
{content_data}
---

위의 구조 설계도에 따라, 콘텐츠 데이터의 모든 정보를 활용하여 완전한 보고서를 작성해주세요. 각 섹션은 해당하는 주제의 발화들을 종합하여 논리적이고 체계적으로 서술해야 합니다. JSON 형식으로 응답해주세요."""
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """AI 응답 파싱"""
        try:
            # JSON 응답 파싱
            parsed = json.loads(response_text)
            
            # 필수 필드 검증
            if "final_report" not in parsed:
                raise ValueError("final_report 필드가 응답에 없습니다.")
            
            final_report = parsed["final_report"]
            report_metadata = parsed.get("report_metadata", {})
            word_count = parsed.get("word_count")
            
            # 보고서 내용 검증
            if not isinstance(final_report, str) or len(final_report.strip()) == 0:
                raise ValueError("최종 보고서가 비어있거나 유효하지 않습니다.")
            
            if len(final_report) < 500:
                raise ValueError("보고서가 너무 짧습니다 (최소 500자 필요).")
            
            # 단어 수 계산 (제공된 값이 없거나 부정확한 경우)
            if not isinstance(word_count, int) or word_count <= 0:
                word_count = self._count_words(final_report)
            
            # 메타데이터 정규화
            if not isinstance(report_metadata, dict):
                report_metadata = {}
            
            # 기본 메타데이터 설정
            default_metadata = {
                "total_sections": len(re.findall(r'^## ', final_report, re.MULTILINE)),
                "content_type": self._extract_content_type(final_report),
                "topics_covered": self._extract_topics(final_report),
                "word_count_estimate": word_count
            }
            
            # 메타데이터 병합 (기본값으로 누락된 항목 채우기)
            for key, value in default_metadata.items():
                if key not in report_metadata:
                    report_metadata[key] = value
            
            result = {
                "final_report": final_report.strip(),
                "report_metadata": report_metadata,
                "word_count": word_count
            }
            
            # 보고서 품질 검증
            self._validate_report_quality(result)
            
            self.log_debug("📄 보고서 종합 파싱 결과", data={
                "word_count": word_count,
                "total_sections": report_metadata.get("total_sections", 0),
                "content_type": report_metadata.get("content_type", "unknown"),
                "topics_covered_count": len(report_metadata.get("topics_covered", []))
            })
            
            return result
            
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 텍스트 직접 사용 (폴백)
            self.log_warning("⚠️ JSON 파싱 실패, 텍스트 직접 사용", data={
                "error": str(e),
                "response_preview": response_text[:300]
            })
            
            return self._fallback_report_generation(response_text)
        
        except Exception as e:
            self.log_error("❌ 보고서 종합 파싱 오류", data={
                "error": str(e),
                "response_preview": response_text[:300]
            })
            raise ValueError(f"보고서 종합 결과 파싱 실패: {str(e)}")
    
    def _fallback_report_generation(self, text: str) -> Dict[str, Any]:
        """
        JSON 파싱 실패 시 사용하는 기본 보고서 생성
        
        Args:
            text: 생성할 텍스트
            
        Returns:
            기본적인 보고서 결과
        """
        # JSON 관련 문자 정리
        cleaned_text = re.sub(r'^\s*{\s*"final_report"\s*:\s*"', '', text)
        cleaned_text = re.sub(r'",?\s*"report_metadata".*}?\s*$', '', cleaned_text)
        cleaned_text = re.sub(r'^"|"$', '', cleaned_text)  # 시작/끝 따옴표 제거
        cleaned_text = cleaned_text.replace('\\n', '\n')  # 이스케이프 문자 변환
        
        # 기본 보고서 구조가 없으면 추가
        if not cleaned_text.startswith('#'):
            cleaned_text = f"# 종합 분석 보고서\n\n{cleaned_text}"
        
        # 최소 길이 보장
        if len(cleaned_text) < 500:
            cleaned_text += "\n\n## 추가 정보\n\n원본 응답 파싱에 실패하여 기본 형태로 제공됩니다. 보다 상세한 분석을 위해서는 재처리가 필요할 수 있습니다."
        
        word_count = self._count_words(cleaned_text)
        
        return {
            "final_report": cleaned_text,
            "report_metadata": {
                "total_sections": len(re.findall(r'^## ', cleaned_text, re.MULTILINE)),
                "content_type": "일반",
                "topics_covered": ["주요 내용"],
                "word_count_estimate": word_count,
                "parsing_note": "JSON 파싱 실패로 인한 폴백 처리"
            },
            "word_count": word_count
        }
    
    def _count_words(self, text: str) -> int:
        """텍스트의 단어 수 계산"""
        # Markdown 형식 제거 후 단어 수 계산
        clean_text = re.sub(r'[#*`>-]', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # 한글과 영어 모두 고려한 단어 수 계산
        korean_chars = len(re.findall(r'[가-힣]', clean_text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', clean_text))
        numbers = len(re.findall(r'\b\d+\b', clean_text))
        
        # 한글은 글자 수, 영어는 단어 수로 계산
        return korean_chars + english_words + numbers
    
    def _extract_content_type(self, text: str) -> str:
        """보고서에서 콘텐츠 유형 추출"""
        # 일반적인 콘텐츠 유형 키워드 검색
        content_types = {
            '토론': ['토론', '논쟁', '찬반', '의견'],
            '강의': ['강의', '교육', '설명', '학습'],
            '인터뷰': ['인터뷰', '질문', '답변', 'Q&A'],
            '뉴스': ['뉴스', '보도', '사건', '발표'],
            '리뷰': ['리뷰', '평가', '분석', '검토'],
            '브이로그': ['일상', '경험', '여행', '생활']
        }
        
        for content_type, keywords in content_types.items():
            for keyword in keywords:
                if keyword in text:
                    return content_type
        
        return '일반'
    
    def _extract_topics(self, text: str) -> List[str]:
        """보고서에서 주요 주제 추출"""
        topics = []
        
        # 섹션 제목에서 주제 추출
        section_titles = re.findall(r'^### (.+)$', text, re.MULTILINE)
        topics.extend(section_titles)
        
        # 주요 키워드 추출 (간단한 패턴)
        common_topics = [
            '주식', '투자', '경제', '정치', '기술', '사회', '문화', '스포츠',
            '게임', '영화', '음악', '여행', '음식', '건강', '교육', '환경'
        ]
        
        for topic in common_topics:
            if topic in text and topic not in topics:
                topics.append(topic)
        
        return topics[:10]  # 최대 10개까지
    
    def _validate_report_quality(self, result: Dict[str, Any]) -> None:
        """생성된 보고서의 품질 검증"""
        final_report = result["final_report"]
        word_count = result["word_count"]
        
        # 기본 구조 검증
        if not final_report.startswith('#'):
            self.log_warning("⚠️ 보고서가 제목(H1)으로 시작하지 않습니다.")
        
        # 섹션 수 검증
        h2_sections = len(re.findall(r'^## ', final_report, re.MULTILINE))
        if h2_sections < 2:
            self.log_warning("⚠️ 보고서의 주요 섹션이 너무 적습니다.", data={
                "section_count": h2_sections
            })
        
        # 길이 검증
        if word_count < 1000:
            self.log_warning("⚠️ 보고서가 상대적으로 짧습니다.", data={
                "word_count": word_count
            })
        elif word_count > 10000:
            self.log_warning("⚠️ 보고서가 상당히 깁니다.", data={
                "word_count": word_count
            })
        
        # 내용 다양성 검증
        unique_sentences = len(set(re.split(r'[.!?]', final_report)))
        repetition_ratio = 1 - (unique_sentences / max(1, len(re.split(r'[.!?]', final_report))))
        
        if repetition_ratio > 0.3:
            self.log_warning("⚠️ 보고서에 반복적인 내용이 많을 수 있습니다.", data={
                "repetition_ratio": repetition_ratio
            })
    
    def _validate_agent_specific_input(self, data: Dict[str, Any]) -> None:
        """보고서 종합 에이전트 특화 입력 검증"""
        required_fields = ["topic_clusters", "report_structure", "content_type"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"{field} 필드가 입력 데이터에 없습니다.")
        
        topic_clusters = data["topic_clusters"]
        report_structure = data["report_structure"]
        content_type = data["content_type"]
        
        # 주제 클러스터 검증
        if not isinstance(topic_clusters, list) or len(topic_clusters) == 0:
            raise ValueError("주제 클러스터 데이터가 비어있거나 유효하지 않습니다.")
        
        # 보고서 구조 검증
        if not isinstance(report_structure, list) or len(report_structure) == 0:
            raise ValueError("보고서 구조 데이터가 비어있거나 유효하지 않습니다.")
        
        # 콘텐츠 유형 검증
        if not isinstance(content_type, str) or len(content_type.strip()) == 0:
            raise ValueError("콘텐츠 유형이 유효하지 않습니다.")
        
        # 각 클러스터의 발화 수 확인
        total_utterances = sum(len(cluster.get("related_utterances", [])) for cluster in topic_clusters)
        if total_utterances == 0:
            raise ValueError("주제 클러스터에 발화 데이터가 없습니다.")
        
        if total_utterances < 5:
            self.log_warning("⚠️ 발화 데이터가 적어 상세한 보고서 생성이 어려울 수 있습니다.", data={
                "total_utterances": total_utterances
            })
    
    def _validate_agent_specific_output(self, result: Dict[str, Any]) -> None:
        """보고서 종합 에이전트 특화 출력 검증"""
        if "final_report" not in result:
            raise ValueError("final_report 필드가 출력에 없습니다.")
        
        final_report = result["final_report"]
        
        if not isinstance(final_report, str) or len(final_report.strip()) == 0:
            raise ValueError("최종 보고서가 비어있거나 유효하지 않습니다.")
        
        if len(final_report) < 300:
            raise ValueError("보고서가 너무 짧습니다.")
        
        # Markdown 기본 구조 검증
        if '#' not in final_report:
            raise ValueError("보고서에 제목 구조가 없습니다.")
        
        # 메타데이터 검증
        if "word_count" not in result or not isinstance(result["word_count"], int):
            raise ValueError("단어 수 정보가 유효하지 않습니다.")