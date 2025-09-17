"""
사용자 닉네임 관련 데이터 모델
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class NicknameCheckRequest(BaseModel):
    """닉네임 중복 확인 요청"""
    nickname: str = Field(..., min_length=2, max_length=20, description="확인할 닉네임")


class NicknameCheckResponse(BaseModel):
    """닉네임 중복 확인 응답"""
    exists: bool = Field(..., description="닉네임 존재 여부")
    message: str = Field(..., description="응답 메시지")


class NicknameLoginRequest(BaseModel):
    """닉네임 로그인/등록 요청"""
    nickname: str = Field(..., min_length=2, max_length=20, description="닉네임")


class NicknameLoginResponse(BaseModel):
    """닉네임 로그인/등록 응답"""
    id: str = Field(..., description="사용자 ID")
    nickname: str = Field(..., description="닉네임")
    createdAt: datetime = Field(..., description="생성 시간")
    isNew: bool = Field(..., description="신규 사용자 여부")


class User(BaseModel):
    """사용자 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="사용자 ID")
    nickname: str = Field(..., description="닉네임")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "nickname": "Rex",
                "created_at": "2025-09-08T12:00:00"
            }
        }