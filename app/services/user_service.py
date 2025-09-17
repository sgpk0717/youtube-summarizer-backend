"""
사용자 닉네임 관리 서비스
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from supabase import create_client, Client
from app.utils.logger import setup_logger
from app.models.user import User

logger = setup_logger("user_service")


class UserService:
    """사용자 관리 서비스"""
    
    def __init__(self):
        """UserService 초기화"""
        logger.info("🚀 UserService 초기화 시작")
        
        # Supabase 클라이언트 초기화
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key:
            try:
                self.supabase: Client = create_client(supabase_url, supabase_key)
                self.enabled = True
                logger.info("✅ Supabase 연결 성공")
                
                # 테이블 초기화 확인
                self._ensure_tables()
                
            except Exception as e:
                logger.error(f"❌ Supabase 연결 실패: {e}")
                self.supabase = None
                self.enabled = False
        else:
            logger.warning("⚠️ Supabase 환경변수 없음 - 메모리 모드로 실행")
            self.supabase = None
            self.enabled = False
            self.memory_users = {}  # 메모리 저장소
    
    def _ensure_tables(self):
        """필요한 테이블이 있는지 확인하고 없으면 생성"""
        try:
            # nicknames 테이블 존재 확인
            result = self.supabase.table('nicknames').select('id').limit(1).execute()
            logger.info("✅ nicknames 테이블 확인 완료")
        except Exception as e:
            logger.warning(f"⚠️ nicknames 테이블 접근 실패: {e}")
            # 테이블이 없으면 SQL로 생성 시도
            try:
                self.supabase.rpc('create_nicknames_table').execute()
                logger.info("✅ nicknames 테이블 생성 완료")
            except:
                logger.warning("⚠️ 테이블 자동 생성 실패 - 수동 생성 필요")
    
    async def check_nickname(self, nickname: str) -> Dict[str, Any]:
        """
        닉네임 중복 확인 (대소문자 무시)
        
        Args:
            nickname: 확인할 닉네임
            
        Returns:
            중복 여부와 메시지
        """
        logger.info(f"🔍 닉네임 중복 확인 시작: {nickname}")
        
        try:
            if self.enabled and self.supabase:
                # Supabase에서 대소문자 무시하고 검색
                result = self.supabase.table('nicknames')\
                    .select('*')\
                    .ilike('nickname', nickname)\
                    .execute()
                
                exists = len(result.data) > 0
                logger.info(f"📊 DB 조회 결과", extra={"data": {
                    "nickname": nickname,
                    "exists": exists,
                    "count": len(result.data)
                }})
            else:
                # 메모리 모드
                exists = any(
                    u['nickname'].lower() == nickname.lower() 
                    for u in self.memory_users.values()
                )
                logger.info(f"📊 메모리 조회 결과: {exists}")
            
            message = "이미 사용 중인 닉네임입니다" if exists else "사용 가능한 닉네임입니다"
            
            return {
                "exists": exists,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"❌ 닉네임 확인 중 오류", extra={"data": {"error": str(e)}})
            raise
    
    async def login_or_register(self, nickname: str) -> Dict[str, Any]:
        """
        닉네임으로 로그인 또는 등록
        
        Args:
            nickname: 닉네임
            
        Returns:
            사용자 정보와 신규 여부
        """
        logger.info(f"🔐 로그인/등록 시작: {nickname}")
        
        try:
            if self.enabled and self.supabase:
                # DB에서 기존 사용자 검색
                result = self.supabase.table('nicknames')\
                    .select('*')\
                    .ilike('nickname', nickname)\
                    .execute()
                
                if result.data:
                    # 기존 사용자 로그인
                    user = result.data[0]
                    logger.info(f"✅ 기존 사용자 로그인", extra={"data": {
                        "id": user['id'],
                        "nickname": user['nickname']
                    }})
                    
                    return {
                        "id": user['id'],
                        "nickname": user['nickname'],
                        "createdAt": user['created_at'],
                        "isNew": False
                    }
                else:
                    # 신규 사용자 등록
                    new_user = {
                        "id": str(uuid.uuid4()),
                        "nickname": nickname,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    result = self.supabase.table('nicknames').insert(new_user).execute()
                    user = result.data[0]
                    
                    logger.info(f"✅ 신규 사용자 등록", extra={"data": {
                        "id": user['id'],
                        "nickname": user['nickname']
                    }})
                    
                    return {
                        "id": user['id'],
                        "nickname": user['nickname'],
                        "createdAt": user['created_at'],
                        "isNew": True
                    }
            else:
                # 메모리 모드
                # 기존 사용자 찾기
                for user_id, user in self.memory_users.items():
                    if user['nickname'].lower() == nickname.lower():
                        logger.info(f"✅ 메모리 - 기존 사용자 로그인: {user_id}")
                        return {
                            "id": user_id,
                            "nickname": user['nickname'],
                            "createdAt": user['created_at'],
                            "isNew": False
                        }
                
                # 신규 사용자 등록
                user_id = str(uuid.uuid4())
                new_user = {
                    "nickname": nickname,
                    "created_at": datetime.now().isoformat()
                }
                self.memory_users[user_id] = new_user
                
                logger.info(f"✅ 메모리 - 신규 사용자 등록: {user_id}")
                
                return {
                    "id": user_id,
                    "nickname": nickname,
                    "createdAt": new_user['created_at'],
                    "isNew": True
                }
                
        except Exception as e:
            logger.error(f"❌ 로그인/등록 중 오류", extra={"data": {"error": str(e)}})
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        사용자 ID로 정보 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            사용자 정보 또는 None
        """
        logger.info(f"🔍 사용자 조회: {user_id}")
        
        try:
            if self.enabled and self.supabase:
                result = self.supabase.table('nicknames')\
                    .select('*')\
                    .eq('id', user_id)\
                    .execute()
                
                if result.data:
                    user = result.data[0]
                    logger.info(f"✅ 사용자 찾음: {user['nickname']}")
                    return user
                else:
                    logger.warning(f"⚠️ 사용자 없음: {user_id}")
                    return None
            else:
                # 메모리 모드
                user = self.memory_users.get(user_id)
                if user:
                    logger.info(f"✅ 메모리 - 사용자 찾음: {user['nickname']}")
                    return {"id": user_id, **user}
                else:
                    logger.warning(f"⚠️ 메모리 - 사용자 없음: {user_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ 사용자 조회 중 오류", extra={"data": {"error": str(e)}})
            return None