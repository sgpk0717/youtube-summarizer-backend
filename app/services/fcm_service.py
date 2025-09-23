"""
FCM (Firebase Cloud Messaging) 서비스
푸시 알림 전송을 위한 서비스
"""
import os
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, messaging
from app.utils.logger import setup_logger, LoggerMixin
from pathlib import Path

logger = setup_logger(__name__)


class FCMService(LoggerMixin):
    """FCM 푸시 알림 서비스"""

    def __init__(self):
        """FCM 서비스 초기화"""
        self.initialized = False
        self.app = None

        try:
            # Firebase 서비스 계정 키 파일 경로
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')

            if not service_account_path:
                # 기본 경로 시도
                default_path = Path(__file__).parent.parent.parent / "firebase-service-account.json"
                if default_path.exists():
                    service_account_path = str(default_path)
                    self.log_info("📱 Firebase 서비스 계정 파일 발견 (기본 경로)")
                else:
                    self.log_warning("⚠️ Firebase 서비스 계정 파일 없음 - FCM 비활성화")
                    return

            # Firebase Admin SDK 초기화
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_path)
                self.app = firebase_admin.initialize_app(cred)
                self.initialized = True
                self.log_info("✅ FCM 서비스 초기화 성공")
            else:
                self.app = firebase_admin.get_app()
                self.initialized = True
                self.log_info("✅ FCM 서비스 이미 초기화됨")

        except FileNotFoundError as e:
            self.log_warning(f"⚠️ Firebase 서비스 계정 파일 없음: {e}")
            self.log_warning("⚠️ FCM 기능이 비활성화됩니다")
        except Exception as e:
            self.log_error(f"❌ FCM 초기화 실패", data={"error": str(e)})
            self.log_warning("⚠️ FCM 기능이 비활성화됩니다")

    async def send_notification(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        FCM 푸시 알림 전송

        Args:
            fcm_token: FCM 클라이언트 토큰
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터 (옵션)

        Returns:
            성공 여부
        """
        if not self.initialized or not fcm_token:
            self.log_warning("🔕 FCM 전송 건너뜀", data={
                "initialized": self.initialized,
                "has_token": bool(fcm_token),
                "token_length": len(fcm_token) if fcm_token else 0,
                "token_preview": fcm_token[:20] + "..." if fcm_token else None
            })
            return False

        try:
            self.log_info("📤 FCM 알림 전송 시작", data={
                "title": title,
                "body": body[:50] + "..." if len(body) > 50 else body,
                "has_data": bool(data),
                "token": fcm_token[:30] + "..." if len(fcm_token) > 30 else fcm_token,
                "token_length": len(fcm_token),
                "data_payload": data
            })

            # 메시지 구성
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        icon='ic_notification',
                        color='#FF0000'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            badge=1,
                            sound='default'
                        )
                    )
                )
            )

            # 메시지 전송
            self.log_info("🚀 FCM 메시지 전송 중...", data={
                "token_used": fcm_token[:30] + "...",
                "title": title
            })

            response = messaging.send(message)

            self.log_info("✅ FCM 알림 전송 성공", data={
                "response": response,
                "message_id": response,
                "token_used": fcm_token[:30] + "...",
                "delivered_to_fcm": True
            })
            return True

        except messaging.UnregisteredError:
            self.log_warning("⚠️ FCM 토큰이 등록 해제됨", data={
                "token": fcm_token[:30] + "...",
                "error_detail": "Token is no longer registered"
            })
            return False
        except messaging.SenderIdMismatchError:
            self.log_warning("⚠️ FCM Sender ID 불일치", data={
                "token": fcm_token[:30] + "...",
                "error_detail": "Sender ID doesn't match"
            })
            return False
        except Exception as e:
            self.log_error("❌ FCM 전송 실패", data={
                "error": str(e),
                "error_type": type(e).__name__,
                "token_tried": fcm_token[:30] + "...",
                "title": title,
                "body": body[:50] + "..."
            })
            return False

    async def send_analysis_complete_notification(
        self,
        fcm_token: str,
        video_title: str,
        video_id: str
    ) -> bool:
        """
        분석 완료 알림 전송

        Args:
            fcm_token: FCM 클라이언트 토큰
            video_title: 영상 제목
            video_id: 영상 ID

        Returns:
            성공 여부
        """
        if not fcm_token:
            self.log_warning("🔕 FCM 토큰 없음 - 알림 전송 건너뜀", data={
                "video_title": video_title,
                "video_id": video_id
            })
            return False

        self.log_info("🎬 분석 완료 알림 준비", data={
            "fcm_token": fcm_token[:30] + "...",
            "video_title": video_title,
            "video_id": video_id
        })

        title = "🎉 분석 완료!"
        body = f"{video_title} 영상 분석이 완료되었습니다. 결과를 확인해보세요!"
        data = {
            "type": "analysis_complete",
            "video_id": video_id,
            "video_title": video_title
        }

        result = await self.send_notification(fcm_token, title, body, data)

        self.log_info("🎬 분석 완료 알림 결과", data={
            "success": result,
            "video_id": video_id
        })

        return result

    def is_available(self) -> bool:
        """FCM 서비스 사용 가능 여부"""
        return self.initialized


# 싱글톤 인스턴스
_fcm_service: Optional[FCMService] = None


def get_fcm_service() -> FCMService:
    """FCM 서비스 인스턴스 가져오기"""
    global _fcm_service
    if _fcm_service is None:
        _fcm_service = FCMService()
    return _fcm_service