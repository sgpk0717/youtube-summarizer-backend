# 개발 워크플로우 가이드

## 🔄 macOS 개발 → Windows 실행 워크플로우

### 개요
- **개발**: macOS에서 편하게 코드 작성
- **실행/테스트**: Windows PC에서 실제 환경 테스트
- **연동**: GitHub를 통한 자동 동기화

---

## 📱 초기 설정 (1회만)

### Windows PC 설정
```powershell
# 1. 프로젝트 클론
cd C:\
git clone https://github.com/sgpk0717/youtube-summarizer-backend.git youtube-summarizer

# 2. 백엔드 디렉토리로 이동
cd youtube-summarizer\backend

# 3. Python 가상환경 생성
python -m venv venv

# 4. 가상환경 활성화
.\venv\Scripts\activate

# 5. 패키지 설치
pip install -r requirements.txt

# 6. 환경변수 설정
copy .env.example .env
# .env 파일 편집하여 쿠키 경로 등 설정
```

---

## 🚀 일일 개발 프로세스

### Step 1: macOS에서 개발
```bash
# 1. 코드 수정
code .  # VS Code로 편집

# 2. 로컬 테스트 (선택사항)
python run.py

# 3. 변경사항 커밋
git add .
git commit -m "feat: 기능 추가"

# 4. GitHub에 푸시
git push origin main
```

### Step 2: Windows에서 실행
```cmd
# 방법 1: 업데이트 스크립트 사용 (권장)
C:\youtube-summarizer\backend\scripts\windows_update_and_run.bat

# 방법 2: 수동 업데이트
cd C:\youtube-summarizer\backend
git pull origin main
venv\Scripts\activate
python run.py --host 0.0.0.0 --port 8000
```

---

## 📝 개발 팁

### 1. 실시간 동기화
Windows PowerShell에서 자동 업데이트 스크립트:
```powershell
# watch_and_run.ps1
while($true) {
    git pull origin main
    Clear-Host
    Write-Host "최신 코드로 업데이트됨. 재시작 중..."
    python run.py --host 0.0.0.0 --port 8000
    Start-Sleep -Seconds 5
}
```

### 2. 브랜치 활용
```bash
# macOS: 기능 브랜치에서 개발
git checkout -b feature/멤버십-자막-추출
# ... 개발 ...
git push origin feature/멤버십-자막-추출

# Windows: 브랜치 테스트
git fetch origin
git checkout feature/멤버십-자막-추출
python run.py
```

### 3. 환경별 설정 분리
```python
# .env.mac (macOS 개발용)
DEBUG=true
COOKIE_PATH=./test_cookies.txt

# .env.windows (Windows 실행용)
DEBUG=false
COOKIE_PATH=C:\Users\사용자명\cookies\youtube.txt
```

---

## 🔍 디버깅 워크플로우

### macOS에서 디버깅 코드 추가
```python
# 디버그 로그 추가
import platform
if platform.system() == "Darwin":  # macOS
    logger.debug("🍎 macOS 디버그 모드")
else:  # Windows
    logger.info("🪟 Windows 실행 모드")
```

### Windows에서 로그 확인
```cmd
# 실시간 로그 모니터링
type C:\youtube-summarizer\backend\logs\2025_09_17_14.txt
# 또는 PowerShell에서
Get-Content logs\*.txt -Tail 50 -Wait
```

---

## ⚡ 빠른 테스트 명령어

### macOS (개발)
```bash
# 구문 검사만
python -m py_compile app/**/*.py

# 빠른 푸시
git add . && git commit -m "test" && git push
```

### Windows (실행)
```cmd
# 빠른 업데이트 및 실행
C:\youtube-summarizer\backend\scripts\windows_quick_test.bat
```

---

## 🛠️ 문제 해결

### "git pull 충돌 발생"
```cmd
# Windows에서 로컬 변경 취소
git stash
git pull origin main
git stash pop  # 필요시
```

### "패키지 버전 불일치"
```cmd
# Windows에서 패키지 재설치
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### "인코딩 문제"
```python
# 크로스 플랫폼 인코딩 처리
with open(file, 'r', encoding='utf-8') as f:
    content = f.read()
```

---

## 📊 권장 도구

### macOS 개발 도구
- **VS Code**: 코드 편집
- **Postman**: API 테스트
- **Git Tower**: Git GUI

### Windows 실행 도구
- **Windows Terminal**: 멋진 터미널
- **Tailscale**: VPN 연결
- **Process Monitor**: 프로세스 모니터링

---

## 🔄 자동화 스크립트

### GitHub Actions (선택사항)
`.github/workflows/notify.yml`:
```yaml
name: Notify Windows
on:
  push:
    branches: [main]
jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Notify Windows PC
        run: |
          # Windows PC에 알림 전송 (Webhook 등)
          echo "Code updated!"
```

---

## 📋 체크리스트

개발 시작 전:
- [ ] macOS: 최신 코드 pull
- [ ] Windows: Tailscale 연결 확인
- [ ] Windows: 쿠키 파일 유효성 확인

개발 후:
- [ ] macOS: 코드 push
- [ ] Windows: pull 및 테스트
- [ ] 로그 확인

---

**작성일**: 2025년 9월 17일
**버전**: 1.0.0