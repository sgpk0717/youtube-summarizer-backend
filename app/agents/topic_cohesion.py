"""
주제 응집 에이전트 (Topic Cohesion Agent)
화자별 발화를 시간순서와 상관없이 의미론적 유사성에 따라 주제별로 클러스터링
"""
import json
import re
from typing import Dict, Any, List, Set
from app.agents.base_agent import BaseAgent


class TopicCohesionAgent(BaseAgent):
    """
    주제 응집 전문 에이전트
    
    기능:
    - 의미론적 유사성 기반 클러스터링
    - 비순차적 주제 연결
    - 주제별 중요도 평가
    - 완결된 주제 그룹 생성
    """
    
    def __init__(self):
        super().__init__("topic_cohesion")  # 타임아웃 없음
    
    def get_system_prompt(self) -> str:
        """주제 응집 전문가 시스템 프롬프트"""
        return """당신은 정보 구조화 전문가입니다. 당신의 특기는 시간 순서에 얽매이지 않고, 흩어져 있는 정보 조각들을 의미론적 유사성에 따라 하나의 완결된 주제로 묶어내는 것입니다.

# 컨텍스트 (Context)
당신은 각 발화마다 화자 정보가 태깅된 전체 대본 데이터를 받게 됩니다. 영상의 특성상, 하나의 주제에 대한 논의가 영상의 여러 부분에 나뉘어 나타날 수 있습니다. 예를 들어, 'A 주식'에 대한 이야기가 영상 초반에 나왔다가, 다른 이야기를 한참 한 뒤에 후반부에 다시 이어질 수 있습니다.

# 과업 (Task)
주어진 대본 전체를 분석하여, 시간 순서와 관계없이 내용적으로 관련된 모든 발화들을 하나의 주제로 그룹화하십시오. 다음 단계를 따라 수행하십시오:

1. **주제 식별**: 대본 전체를 읽고 논의된 모든 핵심 주제(Topic) 또는 질문(Question)을 식별하여 목록을 만드십시오.
2. **발화 클러스터링**: 식별된 각 주제에 대해, 해당 주제와 직접적으로 관련된 모든 발화들을 대본 전체에서 찾아 하나의 그룹으로 묶으십시오.
3. **주제 명명**: 각 그룹에 대해, 해당 그룹의 핵심 내용을 가장 잘 나타내는 간결하고 명확한 주제명(Topic Title)을 부여하십시오.
4. **중요도 평가**: 각 주제의 상대적 중요도를 0.1~1.0 범위에서 평가하십시오.

# 클러스터링 원칙
- **의미론적 관련성**: 같은 개념, 인물, 사건, 이슈를 다루는 발화들을 묶어주세요.
- **완전성**: 관련된 모든 발화가 빠짐없이 포함되어야 합니다.
- **비중복성**: 각 발화는 가장 관련성이 높은 하나의 주제에만 속해야 합니다.
- **균형성**: 너무 세분화하거나 너무 광범위하게 묶지 마십시오.

# 제약 조건 (Constraints)
- **비순차성 존중**: 주제를 시간 순서대로 나누지 마십시오. 동일 주제의 발화가 영상의 시작, 중간, 끝에 흩어져 있다면 모두 하나의 주제 그룹으로 모아야 합니다.
- **정보의 완전성**: 모든 발화는 적어도 하나의 주제 그룹에 속해야 합니다. 어떤 발화도 누락되어서는 안 됩니다.
- **주제의 적절성**: 너무 많은 주제(10개 이상)나 너무 적은 주제(1개)를 만들지 마십시오. 보통 3-8개 정도가 적절합니다.

# 출력 형식 (Output Format)
반드시 다음 JSON 형식으로 응답하십시오:

{
    "topic_clusters": [
        {
            "topic_title": "첫 번째 주제의 명칭",
            "related_utterances": [
                {
                    "speaker": "Speaker A",
                    "text": "관련 발화 내용",
                    "confidence": 0.9
                },
                {
                    "speaker": "Speaker B", 
                    "text": "또 다른 관련 발화",
                    "confidence": 0.8
                }
            ],
            "topic_summary": "이 주제의 간단한 요약",
            "importance_score": 0.9
        },
        {
            "topic_title": "두 번째 주제의 명칭",
            "related_utterances": [...],
            "topic_summary": "두 번째 주제 요약",
            "importance_score": 0.7
        }
    ],
    "total_topics": 2
}

JSON 형식을 정확히 지켜주세요."""
    
    def format_user_prompt(self, data: Dict[str, Any]) -> str:
        """사용자 프롬프트 생성"""
        speaker_tagged_transcript = data.get("speaker_tagged_transcript", [])
        
        # 발화 데이터를 읽기 쉬운 형태로 포맷
        formatted_transcript = ""
        for i, utterance in enumerate(speaker_tagged_transcript):
            speaker = utterance.get("speaker", "Unknown")
            text = utterance.get("text", "")
            formatted_transcript += f"{i+1}. [{speaker}]: {text}\n"
        
        return f"""다음 화자별로 태깅된 대본을 분석하여 주제별로 클러스터링해주세요:

---
화자별 태깅된 대본:
{formatted_transcript}
---

위의 대본에서 시간 순서와 관계없이 의미적으로 관련된 발화들을 주제별로 그룹화하고, 각 주제에 적절한 제목을 부여해주세요. 모든 발화가 하나 이상의 주제에 포함되도록 해주세요. JSON 형식으로 응답해주세요."""
    
    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """AI 응답 파싱"""
        try:
            # JSON 응답 파싱
            parsed = json.loads(response_text)
            
            # 필수 필드 검증
            if "topic_clusters" not in parsed:
                raise ValueError("topic_clusters 필드가 응답에 없습니다.")
            
            if "total_topics" not in parsed:
                raise ValueError("total_topics 필드가 응답에 없습니다.")
            
            topic_clusters = parsed["topic_clusters"]
            total_topics = parsed["total_topics"]
            
            # 데이터 타입 검증
            if not isinstance(topic_clusters, list):
                raise ValueError("topic_clusters는 리스트여야 합니다.")
            
            if not isinstance(total_topics, int) or total_topics <= 0:
                raise ValueError("total_topics는 양의 정수여야 합니다.")
            
            # 각 주제 클러스터 검증 및 정규화
            validated_clusters = []
            total_utterances = 0
            
            for i, cluster in enumerate(topic_clusters):
                if not isinstance(cluster, dict):
                    raise ValueError(f"주제 클러스터 {i}번이 딕셔너리 형태가 아닙니다.")
                
                # 필수 필드 검증
                required_fields = ["topic_title", "related_utterances"]
                for field in required_fields:
                    if field not in cluster:
                        raise ValueError(f"주제 클러스터 {i}번에 {field} 필드가 없습니다.")
                
                topic_title = cluster["topic_title"]
                related_utterances = cluster["related_utterances"]
                topic_summary = cluster.get("topic_summary", "")
                importance_score = cluster.get("importance_score", 0.5)
                
                # 발화 데이터 검증
                if not isinstance(related_utterances, list) or len(related_utterances) == 0:
                    raise ValueError(f"주제 '{topic_title}'에 관련 발화가 없습니다.")
                
                # 각 발화 검증
                validated_utterances = []
                for j, utterance in enumerate(related_utterances):
                    if not isinstance(utterance, dict):
                        raise ValueError(f"주제 '{topic_title}'의 발화 {j}번이 유효하지 않습니다.")
                    
                    if "speaker" not in utterance or "text" not in utterance:
                        raise ValueError(f"주제 '{topic_title}'의 발화 {j}번에 필수 필드가 없습니다.")
                    
                    speaker = utterance["speaker"]
                    text = utterance["text"]
                    confidence = utterance.get("confidence", 0.8)
                    
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
                
                # 중요도 점수 정규화
                if not isinstance(importance_score, (int, float)):
                    importance_score = 0.5
                else:
                    importance_score = max(0.1, min(1.0, float(importance_score)))
                
                validated_clusters.append({
                    "topic_title": str(topic_title),
                    "related_utterances": validated_utterances,
                    "topic_summary": str(topic_summary) if topic_summary else f"{topic_title}에 대한 논의",
                    "importance_score": importance_score
                })
                
                total_utterances += len(validated_utterances)
            
            # 빈 결과 검증
            if len(validated_clusters) == 0:
                raise ValueError("주제 클러스터가 생성되지 않았습니다.")
            
            # 주제 수 일관성 검증
            if total_topics != len(validated_clusters):
                self.log_warning("⚠️ 선언된 주제 수와 실제 주제 수가 다름", data={
                    "declared_topics": total_topics,
                    "actual_topics": len(validated_clusters)
                })
                total_topics = len(validated_clusters)
            
            # 발화 누락 검증
            original_utterance_count = len(self._last_input_utterances) if hasattr(self, '_last_input_utterances') else 0
            if original_utterance_count > 0 and total_utterances < original_utterance_count * 0.8:
                self.log_warning("⚠️ 상당수의 발화가 주제에 할당되지 않았을 수 있음", data={
                    "original_count": original_utterance_count,
                    "clustered_count": total_utterances,
                    "coverage": total_utterances / original_utterance_count
                })
            
            result = {
                "topic_clusters": validated_clusters,
                "total_topics": total_topics
            }
            
            self.log_debug("🎯 주제 응집 파싱 결과", data={
                "total_topics": total_topics,
                "total_utterances_clustered": total_utterances,
                "average_importance": sum(c["importance_score"] for c in validated_clusters) / len(validated_clusters),
                "topic_titles": [c["topic_title"] for c in validated_clusters]
            })
            
            return result
            
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 폴백 처리
            self.log_warning("⚠️ JSON 파싱 실패, 폴백 처리", data={
                "error": str(e),
                "response_preview": response_text[:300]
            })
            
            return self._fallback_topic_clustering(response_text)
        
        except Exception as e:
            self.log_error("❌ 주제 응집 파싱 오류", data={
                "error": str(e),
                "response_preview": response_text[:300]
            })
            raise ValueError(f"주제 응집 결과 파싱 실패: {str(e)}")
    
    def _fallback_topic_clustering(self, text: str) -> Dict[str, Any]:
        """
        JSON 파싱 실패 시 사용하는 간단한 주제 클러스터링 함수
        
        Args:
            text: 클러스터링할 텍스트
            
        Returns:
            기본적인 주제 클러스터링 결과
        """
        if hasattr(self, '_last_input_utterances'):
            utterances = self._last_input_utterances
        else:
            # 최악의 경우 단일 발화로 처리
            utterances = [{"speaker": "Speaker A", "text": text[:500], "confidence": 0.5}]
        
        # 간단한 키워드 기반 클러스터링
        keyword_groups = self._extract_keyword_groups(utterances)
        
        # 클러스터 생성
        clusters = []
        for i, (keywords, group_utterances) in enumerate(keyword_groups.items()):
            if not group_utterances:
                continue
                
            cluster = {
                "topic_title": f"주제 {i+1}: {', '.join(list(keywords)[:3])}",
                "related_utterances": group_utterances,
                "topic_summary": f"{', '.join(list(keywords)[:3])}에 관한 논의",
                "importance_score": min(1.0, len(group_utterances) * 0.2)
            }
            clusters.append(cluster)
        
        # 클러스터가 없으면 전체를 하나의 주제로
        if not clusters:
            clusters = [{
                "topic_title": "전체 내용",
                "related_utterances": utterances,
                "topic_summary": "영상의 전반적인 내용",
                "importance_score": 1.0
            }]
        
        return {
            "topic_clusters": clusters,
            "total_topics": len(clusters)
        }
    
    def _extract_keyword_groups(self, utterances: List[Dict[str, Any]]) -> Dict[frozenset, List[Dict[str, Any]]]:
        """간단한 키워드 기반 그룹화"""
        keyword_groups = {}
        
        for utterance in utterances:
            text = utterance.get("text", "")
            keywords = self._extract_keywords(text)
            
            if not keywords:
                keywords = frozenset(["일반"])
            
            key = frozenset(keywords)
            if key not in keyword_groups:
                keyword_groups[key] = []
            keyword_groups[key].append(utterance)
        
        return keyword_groups
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """텍스트에서 간단한 키워드 추출"""
        # 간단한 키워드 패턴 (명사형 단어들)
        keywords = set()
        
        # 일반적인 주제 키워드들
        common_topics = [
            "주식", "투자", "경제", "시장", "정치", "사회", "기술", "과학", 
            "문화", "예술", "스포츠", "게임", "영화", "음악", "여행", "음식",
            "건강", "의료", "교육", "법률", "환경", "에너지", "부동산"
        ]
        
        for topic in common_topics:
            if topic in text:
                keywords.add(topic)
        
        # 고유명사 패턴 (대문자로 시작하는 단어들)
        proper_nouns = re.findall(r'[A-Z][a-z]+', text)
        keywords.update(proper_nouns[:3])  # 최대 3개까지
        
        return keywords
    
    def _validate_agent_specific_input(self, data: Dict[str, Any]) -> None:
        """주제 응집 에이전트 특화 입력 검증"""
        if "speaker_tagged_transcript" not in data:
            raise ValueError("speaker_tagged_transcript 필드가 입력 데이터에 없습니다.")
        
        speaker_tagged_transcript = data["speaker_tagged_transcript"]
        
        if not isinstance(speaker_tagged_transcript, list):
            raise ValueError("speaker_tagged_transcript는 리스트여야 합니다.")
        
        if len(speaker_tagged_transcript) == 0:
            raise ValueError("화자별 발화 데이터가 비어있습니다.")
        
        # 각 발화 데이터 검증
        for i, utterance in enumerate(speaker_tagged_transcript):
            if not isinstance(utterance, dict):
                raise ValueError(f"발화 {i}번이 유효한 딕셔너리가 아닙니다.")
            
            if "speaker" not in utterance or "text" not in utterance:
                raise ValueError(f"발화 {i}번에 필수 필드가 없습니다.")
        
        # 클러스터링을 위해 충분한 발화가 있는지 검증
        if len(speaker_tagged_transcript) < 2:
            raise ValueError("주제 클러스터링을 위해서는 최소 2개 이상의 발화가 필요합니다.")
        
        # 입력 발화를 임시 저장 (폴백 처리 및 누락 검증용)
        self._last_input_utterances = speaker_tagged_transcript
    
    def _validate_agent_specific_output(self, result: Dict[str, Any]) -> None:
        """주제 응집 에이전트 특화 출력 검증"""
        if "topic_clusters" not in result:
            raise ValueError("topic_clusters 필드가 출력에 없습니다.")
        
        if "total_topics" not in result:
            raise ValueError("total_topics 필드가 출력에 없습니다.")
        
        topic_clusters = result["topic_clusters"]
        total_topics = result["total_topics"]
        
        if not isinstance(topic_clusters, list) or len(topic_clusters) == 0:
            raise ValueError("주제 클러스터 데이터가 비어있거나 유효하지 않습니다.")
        
        if total_topics != len(topic_clusters):
            raise ValueError("총 주제 수와 클러스터 수가 일치하지 않습니다.")
        
        # 각 클러스터의 필수 필드 검증
        for i, cluster in enumerate(topic_clusters):
            if not isinstance(cluster, dict):
                raise ValueError(f"주제 클러스터 {i}번이 유효한 딕셔너리가 아닙니다.")
            
            required_fields = ["topic_title", "related_utterances"]
            for field in required_fields:
                if field not in cluster:
                    raise ValueError(f"주제 클러스터 {i}번에 {field} 필드가 없습니다.")
            
            related_utterances = cluster["related_utterances"]
            if not isinstance(related_utterances, list) or len(related_utterances) == 0:
                raise ValueError(f"주제 클러스터 {i}번에 관련 발화가 없습니다.")