# YouTube Membership OAuth2 설정 가이드

## 🎯 목적
YouTube 멤버십 영상의 자막을 추출하기 위한 OAuth2 인증 설정

## ⚡ 빠른 시작

### Windows PC에서 실행:
```batch
cd backend\scripts
windows_oauth_setup.bat
```

## 📝 상세 설정 절차

### 1️⃣ 사전 준비
- [ ] Python 3.7+ 설치
- [ ] yt-dlp 2024.10.22+ 버전
- [ ] Google 계정 (멤버십 가입된 계정)
- [ ] Tailscale 설치 및 로그인

### 2️⃣ OAuth2 인증 (최초 1회)

#### Windows PC에서:
1. **스크립트 실행**
   ```batch
   backend\scripts\windows_oauth_setup.bat
   ```

2. **디바이스 코드 확인**
   - 콘솔에 표시되는 코드 확인 (예: `ABC-DEF-GHI`)

3. **브라우저에서 인증**
   - https://www.google.com/device 접속
   - 코드 입력
   - Google 계정 로그인
   - "YouTube on TV" 권한 승인

4. **완료 확인**
   - 스크립트가 자동으로 토큰 저장 확인
   - 위치: `%LOCALAPPDATA%\yt-dlp\cache\`

### 3️⃣ 서버 실행

```batch
backend\scripts\windows_run_server.bat
```

서버가 자동으로:
- OAuth2 인증 상태 확인
- 인증되었으면 yt-dlp 서비스 사용
- 미인증시 기본 서비스 사용 (멤버십 영상 불가)

## 🔍 인증 상태 확인

### API 엔드포인트
```
GET http://100.118.223.116:8000/api/auth/oauth2/status
```

### 응답 예시
```json
{
  "authenticated": true,
  "valid": true,
  "message": "토큰 유효",
  "platform": "Windows",
  "expires_in_hours": 23.5
}
```

## ❓ 자주 묻는 질문

### Q: OAuth2 인증은 얼마나 유지되나요?
A: 한 번 인증하면 토큰이 자동 갱신되어 거의 영구적으로 유지됩니다.

### Q: 멤버십이 없는 계정으로 로그인하면?
A: 일반 영상은 볼 수 있지만, 멤버십 영상은 접근할 수 없습니다.

### Q: 토큰이 만료되면?
A: yt-dlp가 자동으로 Refresh Token을 사용해 갱신합니다.

### Q: 다른 계정으로 변경하려면?
A: 캐시를 삭제하고 재인증하세요:
```batch
rmdir /s /q %LOCALAPPDATA%\yt-dlp\cache
windows_oauth_setup.bat
```

## 🚨 문제 해결

### "Sign in to confirm you're not a bot"
- **원인**: 봇 감지
- **해결**: OAuth2 재인증 필요
- **명령**: `windows_oauth_setup.bat` 재실행

### "Members-only content"
- **원인**: 멤버십 미가입
- **해결**: 해당 채널 멤버십 가입 필요

### 토큰 파일을 찾을 수 없음
- **원인**: 인증 실패
- **해결**: 다시 인증 시도

## 📋 체크리스트

### 초기 설정
- [ ] Python 설치 확인
- [ ] yt-dlp 최신 버전 설치
- [ ] FFmpeg 설치 (선택사항)
- [ ] OAuth2 인증 완료
- [ ] 토큰 파일 생성 확인

### 일일 운영
- [ ] 서버 시작 전 OAuth2 상태 확인
- [ ] 에러 로그 모니터링
- [ ] 필요시 토큰 갱신

## 📞 지원

문제가 있으면:
1. `backend/logs/` 폴더의 로그 확인
2. OAuth2 상태 API 호출
3. 스크립트 재실행

---
작성일: 2025년 9월 17일
버전: 1.0