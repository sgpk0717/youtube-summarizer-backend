# 🎬 YouTube Summarizer 완벽 세팅 가이드

## 📋 목차
1. [프로젝트 소개](#-프로젝트-소개)
2. [Windows 세팅 (서버)](#-windows-세팅-서버)
3. [macOS 개발 환경](#-macos-개발-환경)
4. [사용법](#-사용법)
5. [문제 해결](#-문제-해결)

---

## 🎯 프로젝트 소개

유튜브 영상(멤버십 포함)의 자막을 추출하여 AI로 자동 요약하는 개인용 서비스

### 핵심 기능
- ✅ 일반 영상 자막 추출 및 요약
- ✅ **멤버십 영상** 자막 추출 및 요약 (쿠키 인증)
- ✅ 멀티에이전트 시스템으로 고급 분석
- ✅ Tailscale를 통한 원격 접속

### 시스템 구성
- **백엔드 서버**: Windows PC (로컬)
- **개발 환경**: macOS
- **모바일 앱**: Android (React Native)
- **원격 접속**: Tailscale VPN (100.118.223.116)

---

## 🖥️ Windows 세팅 (서버)

### 1️⃣ 사전 준비

#### 필수 설치
- Python 3.8 이상
- Chrome 브라우저
- Git
- Tailscale (선택사항, 원격 접속용)

#### Chrome 설정 (멤버십 영상용)
Chrome 바로가기 → 속성 → 대상 필드 끝에 추가:
```
--disable-features=LockProfileCookieDatabase
```
이렇게 하면 Chrome이 켜진 상태에서도 쿠키를 읽을 수 있습니다.

### 2️⃣ 프로젝트 클론 및 설정

```batch
# 1. 저장소 클론
git clone https://github.com/your-repo/youtube-summarizer.git
cd youtube-summarizer/backend

# 2. 가상환경 생성
python -m venv venv

# 3. 가상환경 활성화
venv\Scripts\activate

# 4. 패키지 설치
pip install -r requirements.txt
```

### 3️⃣ 환경 변수 설정

`.env` 파일 생성:
```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# 서버 설정
HOST=0.0.0.0
PORT=8000

# 프론트엔드 URL (CORS)
FRONTEND_URL=http://localhost:3000

# Supabase (선택사항)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 4️⃣ 쿠키 인증 테스트 (멤버십 영상용)

```batch
# scripts 폴더로 이동
cd scripts

# 쿠키 설정 테스트
windows_cookie_setup.bat
```

성공 메시지가 나오면 준비 완료!

### 5️⃣ 서버 실행

```batch
# scripts 폴더에서
windows_run_server.bat
```

또는 수동 실행:
```batch
cd backend
venv\Scripts\activate
python run.py --host 0.0.0.0 --port 8000
```

---

## 💻 macOS 개발 환경

### 1️⃣ 프로젝트 설정

```bash
# 저장소 클론
git clone https://github.com/your-repo/youtube-summarizer.git
cd youtube-summarizer/backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2️⃣ 개발 서버 실행

```bash
python run.py
```

### 3️⃣ Git 작업 흐름

```bash
# 변경사항 확인
git status

# 변경사항 추가
git add .

# 커밋
git commit -m "feat: 기능 추가"

# 푸시
git push origin main
```

---

## 🚀 사용법

### 서버 접속 주소

#### 로컬 접속
- API: http://localhost:8000
- Swagger 문서: http://localhost:8000/docs
- 쿠키 상태: http://localhost:8000/api/auth/cookie/status

#### Tailscale 원격 접속
- API: http://100.118.223.116:8000
- Swagger 문서: http://100.118.223.116:8000/docs
- 쿠키 상태: http://100.118.223.116:8000/api/auth/cookie/status

### API 사용 예시

#### 1. 쿠키 상태 확인
```bash
curl http://localhost:8000/api/auth/cookie/status
```

응답:
```json
{
  "status": "active",
  "method": "browser (chrome)",
  "can_access_membership": true
}
```

#### 2. 영상 요약 생성
```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=VIDEO_ID"}'
```

응답:
```json
{
  "video_id": "VIDEO_ID",
  "title": "영상 제목",
  "channel": "채널명",
  "duration": "10:23",
  "analysis_result": {
    "summary_extraction": { ... },
    "content_structure": { ... },
    "key_insights": { ... },
    "report_synthesis": {
      "final_report": "종합 분석 보고서..."
    }
  }
}
```

### 멀티에이전트 분석 결과 활용

시스템은 5개의 전문 에이전트가 분석합니다:
1. **요약 추출**: 핵심 내용 요약
2. **구조 분석**: 콘텐츠 구성 파악
3. **인사이트 도출**: 주요 통찰력
4. **실용 가이드**: 실천 방법
5. **종합 보고서**: 통합 분석

---

## 🔧 문제 해결

### Chrome 관련 문제

#### "Chrome이 실행 중입니다" 에러
**해결법 1**: Chrome 완전 종료
```batch
taskkill /F /IM chrome.exe
```

**해결법 2**: Chrome 플래그 추가 (권장)
- Chrome 바로가기 → 속성 → 대상에 추가:
  ```
  --disable-features=LockProfileCookieDatabase
  ```

**해결법 3**: 쿠키 파일로 저장
```batch
cd scripts
windows_cookie_setup.bat
# "쿠키를 파일로 저장하시겠습니까?" → Y
```

### 멤버십 영상 접근 불가

#### 확인사항
1. Chrome에서 YouTube 로그인 상태 확인
2. 해당 채널 멤버십 가입 여부 확인
3. 쿠키 상태 확인:
   ```
   http://localhost:8000/api/auth/cookie/status
   ```

#### 해결 순서
1. Chrome에서 YouTube 로그인
2. 멤버십 영상 재생 테스트
3. Chrome 종료 또는 플래그 추가
4. 서버 재시작

### 서버 시작 실패

#### Python 버전 확인
```batch
python --version
# Python 3.8 이상 필요
```

#### 패키지 재설치
```batch
venv\Scripts\activate
pip install --upgrade -r requirements.txt
```

#### 포트 충돌 해결
```batch
# 8000 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8000

# 프로세스 종료
taskkill /PID [프로세스ID] /F
```

### Tailscale 연결 문제

#### Tailscale 상태 확인
```batch
tailscale status
```

#### IP 주소 확인
```batch
tailscale ip -4
# 100.118.223.116 확인
```

#### 방화벽 설정
- Windows 방화벽에서 8000 포트 허용
- Tailscale 네트워크 인터페이스 신뢰

---

## 📝 추가 정보

### 로그 확인
로그 파일 위치: `backend/logs/YYYY_MM_DD_HH.txt`

실시간 로그 확인:
```batch
type logs\2025_09_18_14.txt
```

### 성능 팁
- 긴 영상은 처리 시간이 오래 걸립니다
- 멤버십 영상은 일반 영상보다 느릴 수 있습니다
- 너무 자주 요청하면 봇으로 감지될 수 있으니 주의

### 보안 주의사항
- API 키는 절대 공개하지 마세요
- `.env` 파일은 `.gitignore`에 포함
- 개인용으로만 사용하세요

---

## 🤝 도움말

문제가 있으시면:
1. 로그 파일 확인 (`backend/logs/`)
2. Chrome 쿠키 상태 확인
3. API 문서 확인 (`/docs`)
4. GitHub Issues에 문의

---

**마지막 업데이트**: 2025년 9월 18일
**방식**: 쿠키 인증 (OAuth2 대체)
**작성자**: YouTube Summarizer Team