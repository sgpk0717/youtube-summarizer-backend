# YouTube Summarizer Backend

유튜브 영상 자막을 추출하여 AI로 요약하는 FastAPI 백엔드 서버

## 🚀 Quick Start

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정:

```env
OPENAI_API_KEY=your_openai_api_key_here
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:3000
```

### 3. 서버 실행

```bash
python run.py
```

서버가 시작되면:
- API: http://localhost:8000
- Swagger 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📡 API 엔드포인트

### POST /api/summarize
유튜브 영상 URL을 받아 요약을 생성합니다.

**Request:**
```json
{
  "url": "https://youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
  "video_id": "VIDEO_ID",
  "title": "영상 제목",
  "channel": "채널명",
  "duration": "10:23",
  "language": "ko",
  "summary": {
    "brief": "한 줄 요약",
    "key_points": ["포인트1", "포인트2", "포인트3"],
    "detailed": "상세 요약 내용"
  },
  "transcript_available": true
}
```

## 🛠️ 기술 스택

- **FastAPI**: 웹 프레임워크
- **youtube-transcript-api**: 자막 추출
- **OpenAI GPT-5.0**: AI 요약 생성
- **Pydantic**: 데이터 검증
- **Uvicorn**: ASGI 서버

## 📁 프로젝트 구조

```
backend/
├── app/
│   ├── main.py              # FastAPI 앱
│   ├── models/
│   │   └── summary.py        # 데이터 모델
│   └── services/
│       ├── youtube_service.py    # 유튜브 서비스
│       └── summarizer_service.py # AI 요약 서비스
├── run.py                    # 서버 실행 스크립트
├── requirements.txt          # 패키지 목록
└── .env                      # 환경 변수
```

## ⚠️ 주의사항

1. **API 키**: OpenAI API 키가 필요합니다
2. **자막 제한**: 자막이 없는 영상은 처리할 수 없습니다
3. **언어 지원**: 한국어와 영어 자막을 우선 지원합니다
4. **토큰 제한**: 긴 영상의 경우 자막이 잘릴 수 있습니다

## 🧪 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# 요약 생성 테스트
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}'
```