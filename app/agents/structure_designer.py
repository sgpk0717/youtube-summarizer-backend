"""
보고서 구조 설계 에이전트 (Report Structure Designer Agent)
주제 클러스터 데이터를 분석하여 최적의 보고서 구조와 포맷 결정
"""
import json
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent


class StructureDesignerAgent(BaseAgent):
    """
    보고서 구조 설계 전문 에이전트
    
    기능:
    - 콘텐츠 유형 분석 및 분류
    - 최적 보고서 구조 설계
    - 섹션별 역할 및 순서 정의
    - 구조 결정 근거 제시
    """
    
    def __init__(self):
        super().__init__("structure_designer")  # 타임아웃 없음
    
    def get_system_prompt(self) -> str:
        """보고서 구조 설계 전문가 시스템 프롬프트"""
        return """당신은 콘텐츠 전략가이자 정보 아키텍트입니다. 당신은 주어진 정보의 성격을 파악하고, 독자가 가장 이해하기 쉬운 형태로 정보를 구조화하는 데 능숙합니다.

# 컨텍스트 (Context)
당신은 영상의 전체 내용이 여러 개의 주제 클러스터로 정리된 데이터를 받게 됩니다. 각 클러스터에는 주제명과 관련 발화들이 포함되어 있습니다.

# 과업 (Task)
입력된 주제 클러스터 데이터를 분석하여, 이 영상의 내용을 가장 효과적으로 전달할 수 있는 최종 보고서의 구조를 설계하십시오.

## 1단계: 콘텐츠 유형 분석
발화 내용을 분석하여 이 영상의 전체적인 포맷이 무엇인지 추론하십시오:
- **뉴스/브리핑**: 사건, 정보 전달 위주
- **패널토론**: 여러 관점의 토론, 찬반 논리
- **1인 강의**: 교육적 내용, 체계적 설명
- **인터뷰**: 질문-답변 구조
- **리뷰/분석**: 특정 대상에 대한 평가
- **일상/브이로그**: 개인적 경험, 일상적 내용
- **기타**: 위에 해당하지 않는 독특한 형식

## 2단계: 최적 구조 제안
분석된 콘텐츠 유형에 가장 적합한 보고서 구조를 결정하십시오:

### 뉴스/브리핑 형식
- **개요**: 핵심 사건/정보 요약
- **주요 내용**: 각 주제별 상세 분석
- **관련 인물/기관**: 언급된 주요 인물
- **향후 전망**: 예상 결과나 시사점

### 패널토론 형식
- **토론 개요**: 주제와 참여자 소개
- **주요 논쟁점**: 각 이슈별 찬반 논리
- **참여자별 입장**: 각 발화자의 주장 정리
- **결론**: 합의점과 이견 요약

### 1인 강의 형식  
- **강의 목표**: 전달하고자 하는 핵심 메시지
- **주요 내용**: 체계적 지식 전달
- **핵심 개념**: 중요한 개념과 원리
- **결론**: 학습 요약과 적용 방안

### 인터뷰 형식
- **인터뷰 배경**: 인터뷰 목적과 맥락
- **주요 질문과 답변**: Q&A 구조로 정리
- **인사이트**: 핵심적인 발언과 관점
- **요약**: 인터뷰를 통해 얻은 정보

## 3단계: 구조 템플릿 생성
결정된 구조를 바탕으로, 최종 보고서의 각 섹션이 어떤 정보를 담아야 하는지를 명시하는 상세한 구조 템플릿을 생성하십시오.

# 제약 조건 (Constraints)
- 당신은 내용을 직접 작성하는 것이 아니라, 최종 보고서를 작성할 'Report Synthesis Agent'를 위한 명확한 '설계도'를 제공해야 합니다.
- 제안하는 구조는 입력된 모든 주제 클러스터의 정보를 빠짐없이 담을 수 있어야 합니다.
- 각 섹션은 구체적이고 실행 가능한 지침을 포함해야 합니다.

# 출력 형식 (Output Format)
반드시 다음 JSON 형식으로 응답하십시오:

{
    "content_type": "패널토론",
    "report_structure": [
        {
            "section_name": "토론 개요",
            "section_description": "토론의 배경과 참여자를 소개하는 섹션",
            "required_topics": ["전체 주제", "참여자 정보"],
            "section_order": 1
        },
        {
            "section_name": "주요 논쟁점 분석",
            "section_description": "각 주제별로 제기된 논쟁점과 관련 논의를 정리",
            "required_topics": ["주제1", "주제2", "주제3"],
            "section_order": 2
        }
    ],
    "structure_rationale": "패널토론 형식으로 판단된 이유와 이 구조를 선택한 근거"
}

JSON 형식을 정확히 지켜주세요."""
    
    def format_user_prompt(self, data: Dict[str, Any]) -> str:
        """사용자 프롬프트 생성"""
        topic_clusters = data.get("topic_clusters", [])
        
        # 주제 클러스터 정보를 읽기 쉽게 포맷
        cluster_summary = ""
        for i, cluster in enumerate(topic_clusters):
            topic_title = cluster.get("topic_title", f"주제 {i+1}")
            topic_summary = cluster.get("topic_summary", "")
            importance_score = cluster.get("importance_score", 0.5)
            utterance_count = len(cluster.get("related_utterances", []))
            
            cluster_summary += f"{i+1}. **{topic_title}** (중요도: {importance_score:.1f}, 발화수: {utterance_count})\n"
            if topic_summary:
                cluster_summary += f"   - {topic_summary}\n"
            
            # 대표 발화 몇 개 포함 (구조 설계 참고용)
            utterances = cluster.get("related_utterances", [])[:3]  # 최대 3개
            for utterance in utterances:
                speaker = utterance.get("speaker", "Unknown")
                text = utterance.get("text", "")[:100]  # 100자로 제한
                cluster_summary += f"   - [{speaker}]: {text}...\n"
            cluster_summary += "\n"
        
        return f"""다음 주제 클러스터 데이터를 분석하여 최적의 보고서 구조를 설계해주세요:

---
주제 클러스터 분석:
총 주제 수: {len(topic_clusters)}개

{cluster_summary}
---

위의 주제 클러스터들을 바탕으로:
1. 이 영상의 콘텐츠 유형을 분석하고
2. 가장 적합한 보고서 구조를 설계하며
3. 각 섹션이 어떤 주제를 다뤄야 하는지 명시해주세요.

JSON 형식으로 응답해주세요."""
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """AI 응답 파싱"""
        try:
            # JSON 응답 파싱
            parsed = json.loads(response_text)
            
            # 필수 필드 검증
            required_fields = ["content_type", "report_structure"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"{field} 필드가 응답에 없습니다.")
            
            content_type = parsed["content_type"]
            report_structure = parsed["report_structure"]
            structure_rationale = parsed.get("structure_rationale", "")
            
            # 데이터 타입 검증
            if not isinstance(content_type, str) or len(content_type.strip()) == 0:
                raise ValueError("content_type는 비어있지 않은 문자열이어야 합니다.")
            
            if not isinstance(report_structure, list) or len(report_structure) == 0:
                raise ValueError("report_structure는 비어있지 않은 리스트여야 합니다.")
            
            # 각 섹션 구조 검증 및 정규화
            validated_sections = []
            
            for i, section in enumerate(report_structure):
                if not isinstance(section, dict):
                    raise ValueError(f"보고서 섹션 {i}번이 딕셔너리 형태가 아닙니다.")
                
                # 필수 필드 검증
                section_required_fields = ["section_name", "section_description", "required_topics", "section_order"]
                for field in section_required_fields:
                    if field not in section:
                        raise ValueError(f"섹션 {i}번에 {field} 필드가 없습니다.")
                
                section_name = section["section_name"]
                section_description = section["section_description"]
                required_topics = section["required_topics"]
                section_order = section["section_order"]
                
                # 각 필드 검증
                if not isinstance(section_name, str) or len(section_name.strip()) == 0:
                    raise ValueError(f"섹션 {i}번의 section_name이 유효하지 않습니다.")
                
                if not isinstance(section_description, str) or len(section_description.strip()) == 0:
                    raise ValueError(f"섹션 {i}번의 section_description이 유효하지 않습니다.")
                
                if not isinstance(required_topics, list):
                    raise ValueError(f"섹션 {i}번의 required_topics가 리스트가 아닙니다.")
                
                if not isinstance(section_order, int) or section_order <= 0:
                    raise ValueError(f"섹션 {i}번의 section_order가 유효한 순서가 아닙니다.")
                
                validated_sections.append({
                    "section_name": section_name.strip(),
                    "section_description": section_description.strip(),
                    "required_topics": [str(topic).strip() for topic in required_topics],
                    "section_order": section_order
                })
            
            # 섹션 순서 정렬
            validated_sections.sort(key=lambda x: x["section_order"])
            
            # 중복 순서 검증
            orders = [section["section_order"] for section in validated_sections]
            if len(set(orders)) != len(orders):
                self.log_warning("⚠️ 중복된 섹션 순서가 있어 자동 정렬됩니다.", data={
                    "orders": orders
                })
                # 순서 재할당
                for i, section in enumerate(validated_sections):
                    section["section_order"] = i + 1
            
            result = {
                "content_type": content_type.strip(),
                "report_structure": validated_sections,
                "structure_rationale": structure_rationale.strip() if structure_rationale else f"{content_type} 형식으로 분석되어 해당 구조를 적용했습니다."
            }
            
            self.log_debug("🏗️ 구조 설계 파싱 결과", data={
                "content_type": result["content_type"],
                "total_sections": len(validated_sections),
                "section_names": [s["section_name"] for s in validated_sections],
                "structure_rationale": result["structure_rationale"]
            })
            
            return result
            
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 폴백 처리
            self.log_warning("⚠️ JSON 파싱 실패, 기본 구조 생성", data={
                "error": str(e),
                "response_preview": response_text[:300]
            })
            
            return self._fallback_structure_design()
        
        except Exception as e:
            self.log_error("❌ 구조 설계 파싱 오류", data={
                "error": str(e),
                "response_preview": response_text[:300]
            })
            raise ValueError(f"구조 설계 결과 파싱 실패: {str(e)}")
    
    def _fallback_structure_design(self) -> Dict[str, Any]:
        """
        JSON 파싱 실패 시 사용하는 기본 구조 설계
        
        Returns:
            기본적인 보고서 구조
        """
        # 입력된 주제 수에 따라 기본 구조 결정
        input_topics = []
        if hasattr(self, '_last_input_clusters'):
            input_topics = [cluster.get("topic_title", f"주제 {i+1}") 
                          for i, cluster in enumerate(self._last_input_clusters)]
        
        if not input_topics:
            input_topics = ["주요 내용"]
        
        # 범용 구조 생성
        basic_structure = [
            {
                "section_name": "개요",
                "section_description": "영상의 전반적인 내용과 핵심 메시지를 요약",
                "required_topics": input_topics,
                "section_order": 1
            },
            {
                "section_name": "주요 내용 분석",
                "section_description": "각 주제별로 상세한 내용과 논의사항을 정리",
                "required_topics": input_topics,
                "section_order": 2
            },
            {
                "section_name": "결론 및 시사점",
                "section_description": "영상의 전체적인 결론과 시청자에게 주는 시사점",
                "required_topics": input_topics,
                "section_order": 3
            }
        ]
        
        return {
            "content_type": "일반",
            "report_structure": basic_structure,
            "structure_rationale": "JSON 파싱 실패로 인해 범용 구조를 적용했습니다."
        }
    
    def _validate_agent_specific_input(self, data: Dict[str, Any]) -> None:
        """구조 설계 에이전트 특화 입력 검증"""
        if "topic_clusters" not in data:
            raise ValueError("topic_clusters 필드가 입력 데이터에 없습니다.")
        
        topic_clusters = data["topic_clusters"]
        
        if not isinstance(topic_clusters, list):
            raise ValueError("topic_clusters는 리스트여야 합니다.")
        
        if len(topic_clusters) == 0:
            raise ValueError("주제 클러스터 데이터가 비어있습니다.")
        
        # 각 클러스터 데이터 검증
        for i, cluster in enumerate(topic_clusters):
            if not isinstance(cluster, dict):
                raise ValueError(f"주제 클러스터 {i}번이 유효한 딕셔너리가 아닙니다.")
            
            if "topic_title" not in cluster:
                raise ValueError(f"주제 클러스터 {i}번에 topic_title 필드가 없습니다.")
            
            if "related_utterances" not in cluster:
                raise ValueError(f"주제 클러스터 {i}번에 related_utterances 필드가 없습니다.")
        
        # 입력 클러스터를 임시 저장 (폴백 처리용)
        self._last_input_clusters = topic_clusters
    
    def _validate_agent_specific_output(self, result: Dict[str, Any]) -> None:
        """구조 설계 에이전트 특화 출력 검증"""
        required_fields = ["content_type", "report_structure"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"{field} 필드가 출력에 없습니다.")
        
        content_type = result["content_type"]
        report_structure = result["report_structure"]
        
        if not isinstance(content_type, str) or len(content_type.strip()) == 0:
            raise ValueError("콘텐츠 유형이 유효하지 않습니다.")
        
        if not isinstance(report_structure, list) or len(report_structure) == 0:
            raise ValueError("보고서 구조가 비어있거나 유효하지 않습니다.")
        
        # 각 섹션의 필수 필드 검증
        section_names = set()
        for i, section in enumerate(report_structure):
            if not isinstance(section, dict):
                raise ValueError(f"보고서 섹션 {i}번이 유효한 딕셔너리가 아닙니다.")
            
            required_section_fields = ["section_name", "section_description", "required_topics", "section_order"]
            for field in required_section_fields:
                if field not in section:
                    raise ValueError(f"섹션 {i}번에 {field} 필드가 없습니다.")
            
            section_name = section["section_name"]
            if section_name in section_names:
                raise ValueError(f"중복된 섹션명이 있습니다: {section_name}")
            section_names.add(section_name)