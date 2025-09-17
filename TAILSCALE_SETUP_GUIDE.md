# Tailscale 설치 및 설정 가이드

## 📱 Phase 1: Tailscale 환경 구축

### Step 1: Windows PC에 Tailscale 설치

1. **다운로드**
   - https://tailscale.com/download/windows 접속
   - "Download Tailscale for Windows" 클릭
   - 설치 파일 다운로드

2. **설치**
   - 다운로드된 `tailscale-setup-*.exe` 파일 실행
   - 설치 마법사 진행 (기본 설정 유지)
   - 설치 완료

3. **로그인**
   - 시스템 트레이에서 Tailscale 아이콘 클릭
   - "Log in" 버튼 클릭
   - 브라우저가 열리면 Google 계정으로 로그인
   - "Connect" 클릭하여 네트워크 연결

4. **IP 확인**
   ```cmd
   # CMD 또는 PowerShell에서 실행
   tailscale ip -4
   ```
   출력 예시: `100.64.1.2`

   **⚠️ 이 IP 주소를 꼭 기록해두세요!**

### Step 2: Android 폰에 Tailscale 설치

1. **Play Store에서 설치**
   - Play Store 열기
   - "Tailscale" 검색
   - 설치 및 열기

2. **로그인**
   - "Log in" 터치
   - 같은 Google 계정으로 로그인
   - VPN 권한 요청 시 "확인" 또는 "허용"

3. **연결 확인**
   - 하단 "Machines" 탭 터치
   - Windows PC가 목록에 있는지 확인
   - PC 이름 확인 (예: `desktop-abc123`)

### Step 3: 연결 테스트

#### Windows PC에서 확인
```cmd
# Tailscale 상태 확인
tailscale status

# 출력 예시:
# 100.64.1.2   desktop-abc123  windows  -
# 100.64.1.3   android-phone   android  active
```

#### Python 스크립트로 확인
```bash
# macOS 개발 환경에서
cd ~/youtube-summarizer/backend/scripts
python check_tailscale.py
```

### Step 4: 환경 변수 설정

백엔드 `.env` 파일에 Tailscale IP 추가:
```env
# Tailscale 설정
TAILSCALE_IP=100.64.1.2  # 위에서 확인한 IP 주소
TAILSCALE_ENABLED=true
```

---

## ✅ 체크리스트

### Windows PC
- [ ] Tailscale 설치 완료
- [ ] Google 계정으로 로그인
- [ ] Tailscale IP 확인 (100.x.x.x)
- [ ] 시스템 트레이에 아이콘 표시

### Android 폰
- [ ] Tailscale 앱 설치
- [ ] 같은 Google 계정으로 로그인
- [ ] VPN 권한 허용
- [ ] Windows PC가 기기 목록에 표시

### 연결 확인
- [ ] PC에서 `tailscale status` 실행
- [ ] Android 기기가 목록에 표시
- [ ] 양쪽 모두 "active" 상태

---

## 🔧 문제 해결

### "Tailscale이 실행되지 않음"
```cmd
# Windows 서비스 재시작 (관리자 권한)
net stop Tailscale
net start Tailscale
```

### "로그인이 안 됨"
1. 브라우저에서 https://login.tailscale.com 직접 접속
2. Google 계정으로 로그인
3. Tailscale 앱에서 다시 시도

### "IP가 100.x.x.x가 아님"
- 정상입니다. Tailscale은 100.64.0.0/10 대역을 사용합니다.
- 100.x.x.x 또는 fd7a:xxx:xxx 형태의 IP가 할당됩니다.

### "Android에서 PC가 안 보임"
1. 두 기기가 같은 계정으로 로그인했는지 확인
2. Windows 방화벽 임시 비활성화 후 테스트
3. Tailscale 앱 재시작

---

## 📝 다음 단계

Phase 1이 완료되면:
1. **Phase 2**: Windows PC 환경 설정
2. **Phase 3**: YouTube 쿠키 추출 및 설정
3. **Phase 4**: 백엔드 코드 구현

---

## 📞 추가 도움말

- Tailscale 공식 문서: https://tailscale.com/kb/
- Windows 설치 가이드: https://tailscale.com/kb/1347/installation/#windows
- Android 설치 가이드: https://tailscale.com/kb/1079/install-android/