# YouTube 멤버십 영상 자막 추출 시스템 - OAuth2 구현 계획서

## 📅 작성일: 2025년 9월 17일
## 🔄 버전: 2.0 (OAuth2 기반 재설계)

---

# 🎯 프로젝트 개요

## 목표
YouTube 멤버십 영상의 자막을 안전하게 추출하고 AI로 요약하는 개인용 시스템 구축

## 핵심 변경사항
- ~~쿠키 기반 인증~~ → **OAuth2 인증** (yt-dlp 2024.10.22+ 네이티브 지원)
- 봇 감지 회피를 위한 로컬 Windows 서버 실행
- Tailscale VPN을 통한 안전한 원격 접속

## 시스템 아키텍처
```
┌─────────────────┐
│  Android App    │
│ (React Native)  │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────┐
│  Tailscale VPN  │
│ 100.118.223.116 │
└────────┬────────┘
         │ :8000
         ↓
┌─────────────────┐
│  Windows PC     │
│  FastAPI Server │
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌────────┐ ┌──────────┐
│ yt-dlp │ │ OpenAI   │
│ OAuth2 │ │ API      │
└────────┘ └──────────┘
    ↓         ↓
┌────────┐ ┌──────────┐
│YouTube │ │ GPT-5    │
│  API   │ │ Summary  │
└────────┘ └──────────┘
```

---

# 🔐 OAuth2 인증 시스템 설계

## 1. yt-dlp OAuth2 인증 매커니즘

### 1.1 최신 버전 요구사항
- **yt-dlp 버전**: 2024.10.22 이상 (OAuth2 네이티브 지원)
- **Python 버전**: 3.7+ (yt-dlp 요구사항)
- **Windows**: PowerShell 5.0+ (스크립트 실행용)

### 1.2 OAuth2 인증 플로우
```python
# 기본 명령어 구조
yt-dlp --username oauth2 --password "" [VIDEO_URL]

# Python API 사용시
ydl_opts = {
    'username': 'oauth2',
    'password': '',
    'cachedir': 'C:\\Users\\[USERNAME]\\AppData\\Local\\yt-dlp\\cache',
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['ko', 'en'],
    'skip_download': True,  # 영상 다운로드 스킵, 자막만 추출
}
```

### 1.3 토큰 저장 위치 (Windows)
- **기본 캐시 디렉토리**: `%LOCALAPPDATA%\yt-dlp\cache`
- **실제 경로**: `C:\Users\[USERNAME]\AppData\Local\yt-dlp\cache`
- **토큰 파일**: `youtube-oauth2.token_data`

## 2. 인증 프로세스 상세

### 2.1 최초 인증 (One-Time Setup)
1. **yt-dlp OAuth2 초기화**
   ```cmd
   yt-dlp --username oauth2 --password "" --verbose
   ```

2. **디바이스 코드 발급**
   - 콘솔에 코드 표시: `XXX-YYY-ZZZ`
   - 인증 URL: `https://www.google.com/device`

3. **브라우저 인증**
   - Google 계정으로 로그인
   - 디바이스 코드 입력
   - "YouTube on TV" 권한 승인 (정상)

4. **토큰 저장**
   - 자동으로 캐시 디렉토리에 저장
   - 이후 자동 갱신 (Refresh Token 사용)

### 2.2 토큰 관리 전략

```python
# app/utils/oauth_manager.py
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

class YtDlpOAuthManager:
    def __init__(self):
        self.cache_dir = Path(os.environ['LOCALAPPDATA']) / 'yt-dlp' / 'cache'
        self.token_file = self.cache_dir / 'youtube-oauth2.token_data'

    def is_authenticated(self) -> bool:
        """OAuth2 인증 상태 확인"""
        return self.token_file.exists()

    def get_token_info(self) -> dict:
        """토큰 정보 조회"""
        if not self.is_authenticated():
            return {}

        with open(self.token_file, 'r') as f:
            return json.load(f)

    def initialize_oauth(self) -> tuple[bool, str]:
        """최초 OAuth2 인증 수행"""
        try:
            # yt-dlp OAuth2 인증 명령 실행
            result = subprocess.run(
                ['yt-dlp', '--username', 'oauth2', '--password', '', '--verbose'],
                capture_output=True,
                text=True,
                timeout=300  # 5분 타임아웃
            )

            if result.returncode == 0:
                return True, "OAuth2 인증 성공"
            else:
                return False, result.stderr

        except subprocess.TimeoutExpired:
            return False, "인증 시간 초과 (5분)"
        except Exception as e:
            return False, f"인증 오류: {str(e)}"

    def refresh_token_if_needed(self):
        """필요시 토큰 갱신 (yt-dlp가 자동 처리)"""
        # yt-dlp는 내부적으로 refresh token을 관리함
        # 명시적인 갱신은 불필요
        pass
```

---

# 🛠️ 기술 구현 상세

## 3. Backend 구현 (FastAPI + yt-dlp)

### 3.1 디렉토리 구조
```
backend/
├── app/
│   ├── main.py              # FastAPI 앱
│   ├── services/
│   │   ├── youtube_service.py    # yt-dlp OAuth2 통합
│   │   └── summarizer_service.py # AI 요약
│   ├── utils/
│   │   ├── oauth_manager.py      # OAuth2 관리
│   │   ├── logger.py             # 로깅 시스템
│   │   └── windows_helper.py     # Windows 전용 유틸
│   └── models/
│       └── schemas.py        # Pydantic 모델
├── scripts/
│   ├── windows_oauth_setup.bat   # OAuth2 초기 설정
│   └── check_oauth_status.py     # 인증 상태 확인
└── logs/
    └── 2025_09_17_*.txt     # 시간별 로그
```

### 3.2 핵심 서비스 구현

```python
# app/services/youtube_service.py
import yt_dlp
import json
from pathlib import Path
from typing import Optional, Dict, List
from app.utils.logger import LoggerMixin
from app.utils.oauth_manager import YtDlpOAuthManager

class YouTubeService(LoggerMixin):
    def __init__(self):
        self.oauth_manager = YtDlpOAuthManager()
        self.log_info("🚀 YouTube Service 초기화", data={
            "oauth_status": self.oauth_manager.is_authenticated()
        })

    def extract_subtitles(self, video_url: str) -> Dict:
        """멤버십 영상 자막 추출 (OAuth2 인증)"""

        self.log_info("🎬 자막 추출 시작", data={"url": video_url})

        # OAuth2 인증 확인
        if not self.oauth_manager.is_authenticated():
            self.log_error("❌ OAuth2 인증 필요")
            raise Exception("OAuth2 인증이 필요합니다. 먼저 인증을 완료하세요.")

        # yt-dlp 옵션 설정
        ydl_opts = {
            # OAuth2 인증
            'username': 'oauth2',
            'password': '',

            # 자막 옵션
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['ko', 'en', 'ja'],
            'skip_download': True,  # 영상은 다운로드하지 않음

            # 출력 옵션
            'quiet': False,
            'no_warnings': False,
            'verbose': True,

            # 캐시 설정
            'cachedir': str(self.oauth_manager.cache_dir),

            # 후처리
            'postprocessors': [{
                'key': 'FFmpegSubtitlesConvertor',
                'format': 'srt'  # SRT 형식으로 변환
            }],

            # 진행 상황 후킹
            'progress_hooks': [self._progress_hook],

            # 로거 연결
            'logger': self.get_yt_dlp_logger(),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 영상 정보 추출
                self.log_debug("🔍 영상 정보 추출 중...")
                info = ydl.extract_info(video_url, download=False)

                # 멤버십 영상 확인
                is_membership = info.get('availability') == 'subscriber_only'
                self.log_info(f"📊 멤버십 영상: {is_membership}")

                # 자막 데이터 추출
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})

                # 자막 다운로드 및 파싱
                subtitle_text = self._download_and_parse_subtitles(
                    ydl, info, subtitles, automatic_captions
                )

                result = {
                    'video_id': info.get('id'),
                    'title': info.get('title'),
                    'channel': info.get('channel'),
                    'duration': info.get('duration'),
                    'is_membership': is_membership,
                    'subtitles': subtitle_text,
                    'languages': list(subtitles.keys()) + list(automatic_captions.keys())
                }

                self.log_info("✅ 자막 추출 성공", data={
                    "video_id": result['video_id'],
                    "languages": result['languages'],
                    "subtitle_length": len(subtitle_text)
                })

                return result

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)

            # 봇 감지 오류 처리
            if "Sign in to confirm you're not a bot" in error_msg:
                self.log_error("🤖 봇 감지됨 - OAuth2 재인증 필요")
                # OAuth2 토큰 갱신 시도
                self.oauth_manager.refresh_token_if_needed()
                raise Exception("봇 감지로 인한 인증 실패. OAuth2 재인증이 필요합니다.")

            # 멤버십 권한 오류
            elif "members-only" in error_msg or "subscriber_only" in error_msg:
                self.log_error("🔒 멤버십 권한 없음")
                raise Exception("이 영상은 멤버십 가입이 필요합니다.")

            else:
                self.log_error(f"❌ 다운로드 오류: {error_msg}")
                raise

        except Exception as e:
            self.log_error(f"❌ 예상치 못한 오류: {str(e)}", data={
                "error_type": type(e).__name__,
                "error_details": str(e)
            })
            raise

    def _download_and_parse_subtitles(self, ydl, info, subtitles, automatic_captions):
        """자막 다운로드 및 파싱"""
        subtitle_text = ""

        # 우선순위: 1. 한국어 자막, 2. 영어 자막, 3. 자동 생성 자막
        for lang in ['ko', 'en', 'ja']:
            if lang in subtitles:
                self.log_info(f"📝 {lang} 자막 다운로드 중...")
                subtitle_url = subtitles[lang][0]['url']
                subtitle_text = self._fetch_subtitle_content(subtitle_url)
                break
            elif lang in automatic_captions:
                self.log_info(f"🤖 {lang} 자동 자막 다운로드 중...")
                subtitle_url = automatic_captions[lang][0]['url']
                subtitle_text = self._fetch_subtitle_content(subtitle_url)
                break

        if not subtitle_text:
            self.log_warning("⚠️ 자막을 찾을 수 없음")

        return subtitle_text

    def _fetch_subtitle_content(self, subtitle_url: str) -> str:
        """자막 내용 가져오기"""
        import requests

        try:
            response = requests.get(subtitle_url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.log_error(f"자막 다운로드 실패: {str(e)}")
            return ""

    def _progress_hook(self, d):
        """다운로드 진행 상황 후킹"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            self.log_debug(f"📊 진행률: {percent}")
        elif d['status'] == 'finished':
            self.log_info("✅ 다운로드 완료")

    def get_yt_dlp_logger(self):
        """yt-dlp용 로거 어댑터"""
        class YtDlpLogger:
            def __init__(self, parent):
                self.parent = parent

            def debug(self, msg):
                self.parent.log_debug(f"[yt-dlp] {msg}")

            def warning(self, msg):
                self.parent.log_warning(f"[yt-dlp] {msg}")

            def error(self, msg):
                self.parent.log_error(f"[yt-dlp] {msg}")

        return YtDlpLogger(self)
```

### 3.3 FastAPI 엔드포인트

```python
# app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

from app.services.youtube_service import YouTubeService
from app.services.summarizer_service import SummarizerService
from app.utils.oauth_manager import YtDlpOAuthManager
from app.utils.logger import setup_logger

app = FastAPI(title="YouTube Membership Subtitle Extractor")

# CORS 설정 (Tailscale IP 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://100.118.223.116:3000",  # Tailscale IP
        "http://localhost:3000",         # 개발용
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 초기화
youtube_service = YouTubeService()
summarizer_service = SummarizerService()
oauth_manager = YtDlpOAuthManager()
logger = setup_logger(__name__)

# Request/Response 모델
class SummarizeRequest(BaseModel):
    url: str

class SummarizeResponse(BaseModel):
    video_id: str
    title: str
    channel: str
    is_membership: bool
    summary: dict

class AuthStatus(BaseModel):
    authenticated: bool
    cache_dir: str
    token_exists: bool
    message: str

@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "status": "running",
        "service": "YouTube Membership Subtitle Extractor",
        "oauth_status": oauth_manager.is_authenticated(),
        "tailscale_ip": "100.118.223.116"
    }

@app.get("/api/auth/status", response_model=AuthStatus)
async def get_auth_status():
    """OAuth2 인증 상태 확인"""
    is_auth = oauth_manager.is_authenticated()

    return AuthStatus(
        authenticated=is_auth,
        cache_dir=str(oauth_manager.cache_dir),
        token_exists=oauth_manager.token_file.exists(),
        message="인증됨" if is_auth else "인증 필요"
    )

@app.post("/api/auth/initialize")
async def initialize_oauth(background_tasks: BackgroundTasks):
    """OAuth2 초기 인증 수행"""
    logger.info("🔐 OAuth2 인증 시작")

    if oauth_manager.is_authenticated():
        return {"status": "already_authenticated", "message": "이미 인증되어 있습니다"}

    # 백그라운드에서 인증 프로세스 실행
    # (실제로는 사용자 상호작용이 필요하므로 별도 스크립트 실행 권장)
    success, message = oauth_manager.initialize_oauth()

    if success:
        logger.info("✅ OAuth2 인증 성공")
        return {"status": "success", "message": message}
    else:
        logger.error(f"❌ OAuth2 인증 실패: {message}")
        raise HTTPException(status_code=400, detail=message)

@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize_video(request: SummarizeRequest):
    """YouTube 영상 자막 추출 및 요약"""
    logger.info(f"📥 요약 요청: {request.url}")

    # OAuth2 인증 확인
    if not oauth_manager.is_authenticated():
        raise HTTPException(
            status_code=401,
            detail="OAuth2 인증이 필요합니다. /api/auth/initialize를 먼저 호출하세요."
        )

    try:
        # 1. 자막 추출 (OAuth2 사용)
        video_data = youtube_service.extract_subtitles(request.url)

        # 2. AI 요약 생성
        summary = summarizer_service.generate_summary(
            video_data['subtitles'],
            video_data['title']
        )

        # 3. 응답 생성
        response = SummarizeResponse(
            video_id=video_data['video_id'],
            title=video_data['title'],
            channel=video_data['channel'],
            is_membership=video_data['is_membership'],
            summary=summary
        )

        logger.info(f"✅ 요약 완료: {video_data['title']}")
        return response

    except Exception as e:
        logger.error(f"❌ 요약 실패: {str(e)}")

        # 에러 타입별 처리
        if "봇 감지" in str(e):
            raise HTTPException(status_code=403, detail="봇 감지됨. 재인증이 필요합니다.")
        elif "멤버십" in str(e):
            raise HTTPException(status_code=403, detail="멤버십 권한이 없습니다.")
        else:
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/auth/logout")
async def logout():
    """OAuth2 로그아웃 (캐시 삭제)"""
    import shutil

    try:
        if oauth_manager.cache_dir.exists():
            shutil.rmtree(oauth_manager.cache_dir)
            logger.info("✅ OAuth2 캐시 삭제됨")
            return {"status": "success", "message": "로그아웃되었습니다"}
    except Exception as e:
        logger.error(f"❌ 캐시 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그아웃 실패: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    # Windows에서 실행 (Tailscale IP 사용)
    uvicorn.run(
        app,
        host="0.0.0.0",  # 모든 인터페이스에서 접근 가능
        port=8000,
        log_level="info"
    )
```

---

# 📱 Frontend 구현 (React Native)

## 4. Frontend 수정사항

### 4.1 API 서비스 업데이트

```typescript
// src/services/api.ts
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Tailscale IP 사용
const API_BASE_URL = 'http://100.118.223.116:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60초 타임아웃 (멤버십 영상은 시간이 걸릴 수 있음)
});

// OAuth2 상태 확인
export const checkAuthStatus = async () => {
  try {
    const response = await api.get('/api/auth/status');
    return response.data;
  } catch (error) {
    console.error('Auth status check failed:', error);
    throw error;
  }
};

// 영상 요약 요청
export const summarizeVideo = async (url: string) => {
  try {
    // 먼저 인증 상태 확인
    const authStatus = await checkAuthStatus();
    if (!authStatus.authenticated) {
      throw new Error('OAuth2 인증이 필요합니다');
    }

    const response = await api.post('/api/summarize', { url });

    // 결과 캐싱
    await AsyncStorage.setItem(
      `summary_${response.data.video_id}`,
      JSON.stringify(response.data)
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('인증이 필요합니다. 서버에서 OAuth2 설정을 완료하세요.');
      } else if (error.response?.status === 403) {
        throw new Error(error.response.data.detail || '접근 권한이 없습니다');
      }
    }
    throw error;
  }
};
```

### 4.2 인증 상태 표시 컴포넌트

```tsx
// src/components/AuthStatusIndicator.tsx
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { checkAuthStatus } from '../services/api';

export const AuthStatusIndicator = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const status = await checkAuthStatus();
        setIsAuthenticated(status.authenticated);
      } catch (error) {
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
    // 30초마다 상태 체크
    const interval = setInterval(checkAuth, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return null;

  return (
    <View style={styles.container}>
      <View style={[
        styles.indicator,
        { backgroundColor: isAuthenticated ? '#4CAF50' : '#FF5252' }
      ]} />
      <Text style={styles.text}>
        {isAuthenticated ? 'OAuth2 인증됨' : 'OAuth2 인증 필요'}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
  },
  indicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 8,
  },
  text: {
    fontSize: 12,
    color: '#666',
  },
});
```

---

# 🚀 설치 및 실행 가이드

## 5. Windows PC 설정 (백엔드 서버)

### 5.1 초기 설정 스크립트

```batch
@echo off
REM scripts/windows_oauth_setup.bat
echo ========================================
echo   YouTube OAuth2 초기 설정
echo   Windows 환경
echo ========================================
echo.

REM Python 환경 확인
python --version
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았습니다
    pause
    exit /b 1
)

REM yt-dlp 설치/업데이트
echo [1/4] yt-dlp 설치/업데이트 중...
pip install --upgrade yt-dlp

REM yt-dlp 버전 확인
yt-dlp --version
echo.

REM OAuth2 인증 시작
echo [2/4] OAuth2 인증을 시작합니다...
echo.
echo ┌─────────────────────────────────────────┐
echo │  브라우저가 열리면:                     │
echo │  1. Google 계정으로 로그인              │
echo │  2. 표시된 코드 입력 (XXX-YYY-ZZZ)     │
echo │  3. YouTube on TV 권한 승인            │
echo └─────────────────────────────────────────┘
echo.

REM OAuth2 인증 실행
yt-dlp --username oauth2 --password "" --verbose https://www.youtube.com/watch?v=jNQXAC9IVRw

if errorlevel 1 (
    echo [ERROR] OAuth2 인증 실패
    pause
    exit /b 1
)

echo.
echo [3/4] OAuth2 인증 성공!
echo.

REM 캐시 디렉토리 확인
echo [4/4] 토큰 저장 위치 확인 중...
dir %LOCALAPPDATA%\yt-dlp\cache\youtube-oauth2.* 2>nul

if exist %LOCALAPPDATA%\yt-dlp\cache\youtube-oauth2.token_data (
    echo ✅ 토큰이 정상적으로 저장되었습니다
) else (
    echo ⚠️ 토큰 파일을 찾을 수 없습니다
)

echo.
echo ========================================
echo   설정 완료! 서버를 시작할 수 있습니다.
echo ========================================
pause
```

### 5.2 서버 실행 스크립트 (OAuth2 체크 포함)

```batch
@echo off
REM scripts/windows_run_server.bat
echo ========================================
echo   YouTube Summarizer 서버 시작
echo   OAuth2 인증 모드
echo ========================================
echo.

REM OAuth2 인증 상태 확인
echo [1/3] OAuth2 인증 상태 확인 중...
python scripts\check_oauth_status.py
if errorlevel 1 (
    echo.
    echo ⚠️ OAuth2 인증이 필요합니다!
    echo windows_oauth_setup.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

REM Git 최신 변경사항 가져오기
echo [2/3] GitHub에서 최신 코드 가져오는 중...
git pull origin main

REM 가상환경 활성화
echo [3/3] 서버 시작 중...
call venv\Scripts\activate

REM 서버 실행 (Tailscale IP 바인딩)
python run.py --host 0.0.0.0 --port 8000

pause
```

### 5.3 OAuth2 상태 확인 스크립트

```python
# scripts/check_oauth_status.py
#!/usr/bin/env python3
"""
OAuth2 인증 상태 확인 스크립트
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

def check_oauth_status():
    """OAuth2 토큰 상태 확인"""

    print("=" * 50)
    print("  OAuth2 인증 상태 확인")
    print("=" * 50)

    # 캐시 디렉토리 확인
    cache_dir = Path(os.environ['LOCALAPPDATA']) / 'yt-dlp' / 'cache'
    token_file = cache_dir / 'youtube-oauth2.token_data'

    print(f"\n📁 캐시 디렉토리: {cache_dir}")
    print(f"📄 토큰 파일: {token_file}")

    # 토큰 파일 존재 확인
    if not token_file.exists():
        print("\n❌ OAuth2 토큰이 없습니다.")
        print("   windows_oauth_setup.bat을 실행하여 인증을 완료하세요.")
        sys.exit(1)

    # 토큰 정보 읽기
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)

        print("\n✅ OAuth2 토큰이 존재합니다.")

        # 토큰 정보 표시 (민감한 정보는 제외)
        if 'access_token' in token_data:
            print("   - Access Token: ****" + token_data['access_token'][-10:])
        if 'refresh_token' in token_data:
            print("   - Refresh Token: 있음")
        if 'expires_at' in token_data:
            expires = datetime.fromtimestamp(token_data['expires_at'])
            print(f"   - 만료 시간: {expires}")

            # 만료 여부 확인
            if expires < datetime.now():
                print("   ⚠️ 토큰이 만료되었습니다. 자동 갱신됩니다.")

        print("\n🎉 OAuth2 인증이 정상적으로 설정되어 있습니다!")
        sys.exit(0)

    except json.JSONDecodeError:
        print("\n❌ 토큰 파일이 손상되었습니다.")
        print("   windows_oauth_setup.bat을 다시 실행하세요.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_oauth_status()
```

---

# 🧪 테스트 계획

## 6. 단계별 테스트 시나리오

### 6.1 OAuth2 인증 테스트
1. **초기 인증**
   - `windows_oauth_setup.bat` 실행
   - 브라우저에서 디바이스 코드 입력
   - 토큰 파일 생성 확인

2. **토큰 갱신**
   - 토큰 만료 시뮬레이션
   - 자동 갱신 확인

### 6.2 멤버십 영상 테스트
1. **일반 영상**: 정상 추출 확인
2. **멤버십 영상**: OAuth2로 접근 가능 확인
3. **비공개 영상**: 적절한 오류 메시지 확인

### 6.3 봇 감지 회피 테스트
1. **연속 요청**: 10회 연속 요청 시 정상 동작
2. **다양한 채널**: 여러 채널의 영상 테스트
3. **장시간 실행**: 24시간 연속 실행 테스트

### 6.4 Tailscale 연결 테스트
1. **Android → Windows**: 100.118.223.116:8000 접속
2. **응답 시간**: <2초 내 응답
3. **대용량 자막**: 2시간 영상 자막 전송

---

# ⚠️ 보안 고려사항

## 7. 보안 체크리스트

### 7.1 OAuth2 토큰 보안
- ✅ 토큰은 로컬 캐시에만 저장 (Git 제외)
- ✅ 토큰 파일 권한 제한 (Windows ACL)
- ✅ Refresh Token으로 자동 갱신
- ✅ 민감한 정보 로깅 금지

### 7.2 네트워크 보안
- ✅ Tailscale VPN으로 암호화 통신
- ✅ 특정 IP만 CORS 허용
- ✅ Rate Limiting 구현
- ✅ 요청 검증 및 sanitization

### 7.3 개인정보 보호
- ✅ 개인용 서비스 (외부 공개 금지)
- ✅ 로그에 URL/제목만 저장
- ✅ 자막 내용은 임시 저장 후 삭제

---

# 📊 모니터링 및 유지보수

## 8. 운영 가이드

### 8.1 로그 모니터링
```python
# 로그 위치: backend/logs/YYYY_MM_DD_HH.txt
# 실시간 모니터링 (PowerShell)
Get-Content logs\2025_09_17_14.txt -Tail 50 -Wait
```

### 8.2 문제 해결

| 문제 | 원인 | 해결책 |
|------|------|--------|
| "Sign in required" | OAuth2 토큰 만료/무효 | `windows_oauth_setup.bat` 재실행 |
| "Bot detected" | IP 차단 | Tailscale 재연결, 24시간 대기 |
| "Members only" | 멤버십 미가입 | 해당 채널 멤버십 가입 |
| "Connection refused" | 서버 미실행 | `windows_run_server.bat` 실행 |
| "CORS error" | Tailscale IP 변경 | Frontend API URL 업데이트 |

### 8.3 정기 유지보수
- **일일**: 로그 파일 확인
- **주간**: yt-dlp 업데이트 (`yt-dlp -U`)
- **월간**: 토큰 갱신 상태 확인
- **분기별**: 전체 시스템 백업

---

# 🎯 다음 단계

## 9. 구현 우선순위

### Phase 1: OAuth2 인증 구현 ✅
- [x] 설계서 작성
- [ ] OAuth2 초기 설정 스크립트
- [ ] 토큰 관리 모듈

### Phase 2: Backend 구현
- [ ] YouTube Service (yt-dlp OAuth2)
- [ ] FastAPI 엔드포인트
- [ ] 에러 처리 및 로깅

### Phase 3: Frontend 수정
- [ ] Tailscale IP 연동
- [ ] 인증 상태 표시
- [ ] 에러 메시지 개선

### Phase 4: 테스트
- [ ] 단위 테스트
- [ ] 통합 테스트
- [ ] 24시간 안정성 테스트

---

# 📚 참고 자료

## 10. 관련 문서
- [yt-dlp OAuth2 공식 문서](https://github.com/yt-dlp/yt-dlp)
- [YouTube Data API OAuth2](https://developers.google.com/youtube/v3/guides/authentication)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Tailscale Documentation](https://tailscale.com/kb/)

## 11. 버전 정보
- **yt-dlp**: 2024.10.22+ (OAuth2 네이티브 지원)
- **Python**: 3.7+
- **FastAPI**: 0.100.0+
- **React Native**: 0.72.0+

---

**작성자**: AI Assistant
**최종 수정**: 2025년 9월 17일
**상태**: OAuth2 기반 재설계 완료