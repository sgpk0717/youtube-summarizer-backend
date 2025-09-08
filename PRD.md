=================================
프로젝트 복잡도: Standard
선택 이유: API 개발, 외부 서비스 연동(YouTube, AI), 중간 복잡도의 데이터 처리
=================================

# YouTube Summarizer Backend PRD

## 1. 개요

### 배경
- 유튜브 영상이 길어지면서 핵심 내용만 빠르게 파악하고자 하는 니즈 증가
- 시간이 없는 사용자들을 위한 효율적인 콘텐츠 소비 방법 필요
- AI 기술 발전으로 고품질 자동 요약 가능

### 목적
유튜브 영상 URL만으로 자막을 추출하여 AI 기반 자동 요약을 제공하는 RESTful API 서버 구축

## 2. 목표

### 비즈니스 목표
- 영상 요약 처리 시간 < 10초
- API 응답 시간 < 3초
- 일일 처리 가능 영상 수: 1,000개 이상

### 사용자 가치
- 10-60분 영상을 1-2분 내에 핵심 파악
- 언어 장벽 해결 (한국어/영어 자막 지원)
- 구조화된 요약으로 정보 습득 효율 향상

## 3. 핵심 기능

### 기능 목록
| 우선순위 | 기능 | 설명 |
|---------|------|------|
| P0 | URL 파싱 | YouTube URL에서 비디오 ID 추출 |
| P0 | 자막 추출 | youtube-transcript-api로 자막 데이터 획득 |
| P0 | AI 요약 | OpenAI/Claude API로 요약 생성 |
| P0 | 요약 API | FastAPI 엔드포인트 제공 |
| P1 | 언어 감지 | 한국어/영어 자막 자동 선택 |
| P1 | Swagger 문서 | API 자동 문서화 |
| P2 | 에러 핸들링 | 자막 없음, API 한도 등 처리 |

### User Flow
1. **영상 요약 요청**
   - 클라이언트 → POST /api/summarize (YouTube URL)
   - 서버 → URL 검증 및 비디오 ID 추출
   - 서버 → 자막 데이터 추출
   - 서버 → AI 요약 생성
   - 서버 → 구조화된 요약 응답

2. **에러 처리 시나리오**
   - 잘못된 URL → 400 Bad Request
   - 자막 없음 → 404 Not Found with message
   - AI API 오류 → 503 Service Unavailable

## 4. 기술 요구사항

### 아키텍처
```
Client Request
    ↓
FastAPI Server
    ↓
URL Validator → YouTube Service → AI Service
                      ↓                ↓
              youtube-transcript-api  OpenAI/Claude API
                      ↓                ↓
                  Transcript        Summary
                      ↓                ↓
                    Response Builder
                           ↓
                    JSON Response
```

### API 명세

#### POST /api/summarize
**Request:**
```json
{
  "url": "https://youtube.com/watch?v=VIDEO_ID"
}
```

**Response (200 OK):**
```json
{
  "video_id": "VIDEO_ID",
  "title": "영상 제목",
  "channel": "채널명",
  "duration": "15:30",
  "language": "ko",
  "summary": {
    "brief": "한 줄 요약 (50자 이내)",
    "key_points": [
      "핵심 포인트 1",
      "핵심 포인트 2",
      "핵심 포인트 3"
    ],
    "detailed": "상세 요약 내용 (500자 이내)",
    "timestamps": [
      {
        "time": "00:30",
        "content": "주요 내용"
      }
    ]
  },
  "processed_at": "2024-01-01T12:00:00Z"
}
```

**Error Response:**
```json
{
  "error": {
    "code": "NO_TRANSCRIPT",
    "message": "자막을 찾을 수 없습니다",
    "details": "추가 정보"
  }
}
```

### 기술 스택
- **Framework**: FastAPI 0.104+
- **Python**: 3.9+
- **주요 라이브러리**:
  - youtube-transcript-api: 자막 추출
  - openai/anthropic: AI 요약
  - pydantic: 데이터 검증
  - uvicorn: ASGI 서버
  - python-dotenv: 환경변수 관리

### 성능 요구사항
- 응답 시간: < 3초 (자막 추출 + AI 처리)
- 동시 처리: 10 requests/sec
- 메모리 사용: < 512MB
- CPU 사용률: < 70%

## 5. 환경 설정

### 환경 변수
```env
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Server Config
HOST=0.0.0.0
PORT=8000
WORKERS=4

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60
```

### 보안 요구사항
- API 키 환경변수 관리
- CORS 설정으로 허가된 도메인만 접근
- Rate Limiting 구현
- Input Validation (URL 형식 검증)

## 6. 리스크 및 대응방안

| 리스크 | 영향도 | 대응방안 |
|--------|--------|---------|
| YouTube API 변경 | 높음 | youtube-transcript-api 정기 업데이트 |
| AI API 비용 증가 | 중간 | 캐싱 구현, 토큰 최적화 |
| 자막 없는 영상 | 낮음 | 명확한 에러 메시지 제공 |
| 긴 영상 처리 | 중간 | 청크 단위 처리, 타임아웃 설정 |

## 7. 개발 우선순위

### Phase 1 (MVP)
1. FastAPI 기본 서버 구축
2. YouTube URL 파싱 및 검증
3. 자막 추출 서비스 구현
4. OpenAI/Claude 연동 요약 생성
5. 기본 API 엔드포인트 구현

### Phase 2 (Enhancement)
1. Swagger 자동 문서화
2. 에러 핸들링 고도화
3. 캐싱 메커니즘 구현
4. Rate Limiting 구현
5. 다국어 자막 우선순위 처리

### Phase 3 (Optimization)
1. 비동기 처리 최적화
2. 배치 처리 지원
3. Webhook 지원
4. 요약 품질 개선 (프롬프트 최적화)

## 8. 테스트 계획

### 단위 테스트
- URL 파싱 로직
- 자막 추출 서비스
- AI 요약 서비스

### 통합 테스트
- End-to-End API 테스트
- 에러 시나리오 테스트
- 성능 테스트 (응답 시간)

### 테스트 케이스
```python
# 정상 케이스
- 한국어 자막 영상
- 영어 자막 영상
- 자동 생성 자막 영상

# 에러 케이스
- 잘못된 URL 형식
- 존재하지 않는 비디오
- 자막 없는 영상
- API 한도 초과
```

## 9. 모니터링

### 메트릭
- API 응답 시간
- 일일 요청 수
- 에러율
- AI API 사용량 및 비용

### 로깅
- 모든 요청/응답 로깅
- 에러 상세 로깅
- AI API 호출 로깅

## 10. 문서화

### API 문서
- Swagger UI 자동 생성 (/docs)
- ReDoc 지원 (/redoc)
- Postman Collection 제공

### 개발자 가이드
- 로컬 환경 설정
- API 사용 예제
- 에러 코드 가이드