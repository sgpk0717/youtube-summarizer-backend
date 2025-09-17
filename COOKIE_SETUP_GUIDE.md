# YouTube 쿠키 인증 설정 가이드

## 🎯 OAuth2에서 쿠키로 전환
YouTube가 OAuth2를 막아서 쿠키 방식으로 변경되었습니다.

## ⚡ 빠른 시작 (Windows)

### 1️⃣ Chrome 설정 (한 번만)
Chrome 바로가기 → 속성 → 대상에 추가:
```
--disable-features=LockProfileCookieDatabase
```
이렇게 하면 Chrome이 켜진 상태에서도 작동합니다!

### 2️⃣ 서버 실행
```batch
cd backend\scripts
windows_run_server.bat
```

끝! 이제 멤버십 영상도 처리 가능합니다.

---

## 📝 상세 설정

### Chrome이 켜진 상태에서 사용하려면

#### 방법 1: Chrome 플래그 추가 (권장)
1. Chrome 바로가기 우클릭 → 속성
2. 대상 필드 끝에 추가:
   ```
   --disable-features=LockProfileCookieDatabase
   ```
3. Chrome 재시작

#### 방법 2: 쿠키 파일 저장
1. Chrome 완전 종료
2. 실행:
   ```batch
   cd backend\scripts
   windows_cookie_setup.bat
   ```
3. "쿠키를 파일로 저장하시겠습니까?" → Y
4. 이제 Chrome이 켜져 있어도 사용 가능!

### Chrome을 끌 수 있다면
그냥 Chrome 끄고 서버 실행하면 됩니다. 간단!

## 🔍 작동 원리

```
Chrome 브라우저 (YouTube 로그인)
         ↓
    쿠키 자동 추출
         ↓
      yt-dlp
         ↓
    멤버십 영상 접근
```

## ❓ 자주 묻는 질문

### Q: 쿠키는 얼마나 유지되나요?
A: Chrome이 YouTube에 로그인되어 있는 한 계속 유지됩니다.

### Q: "Chrome이 실행 중입니다" 에러
A: 3가지 해결 방법:
1. Chrome 종료
2. Chrome 플래그 추가 (위 참조)
3. 쿠키 파일 저장 (위 참조)

### Q: 멤버십이 없는 계정이면?
A: 일반 영상만 가능, 멤버십 영상은 접근 불가

### Q: 다른 브라우저 사용 가능?
A: Edge, Firefox도 가능하지만 Chrome이 가장 안정적

## 🚨 주의사항

- 너무 많은 영상을 빠르게 다운로드하지 마세요 (계정 정지 위험)
- 가끔 사용하는 개인용이니 문제없을 것입니다
- Chrome에서 YouTube 로그아웃하면 재로그인 필요

## 📋 체크리스트

- [ ] Chrome에서 YouTube 로그인
- [ ] Chrome 플래그 추가 또는 Chrome 종료
- [ ] 서버 실행
- [ ] 테스트

---
작성일: 2025년 9월 18일
방식: 쿠키 인증 (OAuth2 대체)