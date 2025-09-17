#!/usr/bin/env python3
"""
Tailscale 설치 및 연결 상태 확인 스크립트
Windows와 macOS 모두 지원
"""

import subprocess
import platform
import json
import sys

def check_tailscale_installation():
    """Tailscale 설치 여부 확인"""
    system = platform.system()

    if system == "Windows":
        tailscale_cmd = r"C:\Program Files\Tailscale\tailscale.exe"
    elif system == "Darwin":  # macOS
        tailscale_cmd = "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
    else:
        tailscale_cmd = "tailscale"

    try:
        # tailscale version 명령 실행
        result = subprocess.run(
            [tailscale_cmd, "version"],
            capture_output=True,
            text=True,
            shell=(system == "Windows")
        )

        if result.returncode == 0:
            print("✅ Tailscale이 설치되어 있습니다.")
            print(f"   버전: {result.stdout.strip()}")
            return True, tailscale_cmd
        else:
            print("❌ Tailscale이 설치되지 않았습니다.")
            return False, None

    except FileNotFoundError:
        print("❌ Tailscale이 설치되지 않았습니다.")
        print(f"   다운로드: https://tailscale.com/download/{system.lower()}")
        return False, None
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False, None

def check_tailscale_status(tailscale_cmd):
    """Tailscale 연결 상태 확인"""
    system = platform.system()

    try:
        # tailscale status 명령 실행
        result = subprocess.run(
            [tailscale_cmd, "status", "--json"],
            capture_output=True,
            text=True,
            shell=(system == "Windows")
        )

        if result.returncode == 0:
            status = json.loads(result.stdout)

            # 자신의 정보
            self_info = status.get("Self", {})
            if self_info:
                print("\n📍 내 Tailscale 정보:")
                print(f"   호스트명: {self_info.get('HostName', 'Unknown')}")
                print(f"   IP 주소: {self_info.get('TailscaleIPs', ['Unknown'])[0]}")
                print(f"   온라인 상태: {'✅ 연결됨' if self_info.get('Online') else '❌ 오프라인'}")

            # 연결된 피어 정보
            peers = status.get("Peer", {})
            if peers:
                print("\n👥 연결된 기기들:")
                for peer_id, peer_info in list(peers.items())[:5]:  # 최대 5개만 표시
                    print(f"   - {peer_info.get('HostName', 'Unknown')}: {peer_info.get('TailscaleIPs', ['Unknown'])[0]}")

            return True
        else:
            print("⚠️ Tailscale이 실행 중이지 않습니다.")
            print("   Tailscale 앱을 실행하고 로그인해주세요.")
            return False

    except json.JSONDecodeError:
        print("⚠️ Tailscale 상태를 파싱할 수 없습니다.")
        return False
    except Exception as e:
        print(f"❌ 상태 확인 중 오류: {e}")
        return False

def get_tailscale_ip(tailscale_cmd):
    """Tailscale IP 주소 가져오기"""
    system = platform.system()

    try:
        result = subprocess.run(
            [tailscale_cmd, "ip", "-4"],
            capture_output=True,
            text=True,
            shell=(system == "Windows")
        )

        if result.returncode == 0:
            ip = result.stdout.strip()
            print(f"\n🌐 Tailscale IP 주소: {ip}")
            print(f"   이 IP를 기록해두세요!")
            return ip
        else:
            print("⚠️ IP 주소를 가져올 수 없습니다.")
            return None

    except Exception as e:
        print(f"❌ IP 확인 중 오류: {e}")
        return None

def main():
    print("=" * 50)
    print("  Tailscale 설치 및 연결 상태 확인")
    print("=" * 50)
    print(f"운영체제: {platform.system()} {platform.version()}")
    print()

    # 1. 설치 확인
    installed, tailscale_cmd = check_tailscale_installation()

    if not installed:
        print("\n📌 Tailscale 설치가 필요합니다.")
        print("   위 링크에서 다운로드 후 다시 실행해주세요.")
        sys.exit(1)

    # 2. 상태 확인
    connected = check_tailscale_status(tailscale_cmd)

    if not connected:
        print("\n📌 Tailscale 앱을 실행하고 로그인 후 다시 실행해주세요.")
        sys.exit(1)

    # 3. IP 확인
    ip = get_tailscale_ip(tailscale_cmd)

    if ip:
        print("\n✅ Tailscale 설정이 완료되었습니다!")
        print(f"   백엔드 접속 주소: http://{ip}:8000")

        # 환경변수 설정 파일 생성 제안
        print("\n📝 다음 단계:")
        print("   1. Windows PC와 Android 폰 모두에서 Tailscale 로그인 확인")
        print("   2. 위의 IP 주소를 프론트엔드 설정에 추가")
        print("   3. Windows 방화벽에서 8000 포트 허용")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()