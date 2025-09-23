"""
YouTube Summarizer API - 메인 애플리케이션
FastAPI를 사용한 REST API 서버
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import asyncio
from dotenv import load_dotenv

from app.services.youtube_service import YouTubeService
from app.services.youtube_service_ytdlp import YouTubeServiceYtDlp
from app.services.summarizer_service import SummarizerService
from app.services.database_service import DatabaseService
from app.services.multi_agent_service import MultiAgentService
from app.services.user_service import UserService
from app.services.fcm_service import get_fcm_service
from app.models.summary import SummaryResponse, SummarizeRequest, MultiAgentAnalyzeRequest, MultiAgentAnalyzeResponse
from app.models.user import NicknameCheckResponse, NicknameLoginRequest, NicknameLoginResponse
from app.utils.logger import setup_logger, log_function_call
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# 로거 설정
logger = setup_logger("main")

# FastAPI 앱 초기화
logger.info("🚀 FastAPI 앱 초기화 시작")
app = FastAPI(
    title="YouTube Summarizer API", 
    version="1.0.0",
    description="유튜브 영상을 AI로 요약하는 API 서비스"
)
logger.info("✅ FastAPI 앱 초기화 완료")

# CORS 설정 - 프론트엔드와의 통신을 위해 필요
# Tailscale IP 추가
cors_origins = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
    "http://100.118.223.116:3000",  # Tailscale IP for Android app
    "http://100.118.223.116:8081",  # React Native dev server
]
logger.info(f"📡 CORS 설정 시작", extra={"data": {"allowed_origins": cors_origins}})
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("✅ CORS 설정 완료")

# 서비스 초기화
logger.info("🔧 서비스 초기화 시작")

# YouTube 서비스 선택
# 멤버십 영상을 위해 yt-dlp 서비스 사용 시도
try:
    youtube_service = YouTubeServiceYtDlp()
    logger.info("🍪 yt-dlp 서비스 초기화 (쿠키 인증)")
except Exception as e:
    logger.warning(f"⚠️ yt-dlp 서비스 초기화 실패, 기본 서비스 사용: {e}")
    youtube_service = YouTubeService()

summarizer_service = SummarizerService()
user_service = UserService()

# FCM 서비스 초기화 (옵셔널 - 실패해도 앱 실행에 영향 없음)
fcm_service = get_fcm_service()
if fcm_service.is_available():
    logger.info("✅ FCM 서비스 사용 가능")
else:
    logger.info("ℹ️ FCM 서비스 사용 불가 (푸시 알림 비활성화)")

# 멀티에이전트 서비스 초기화
try:
    multi_agent_service = MultiAgentService()
    logger.info("✅ 멀티에이전트 서비스 초기화 성공")
except Exception as e:
    logger.warning(f"⚠️ 멀티에이전트 서비스 초기화 실패: {e}")
    logger.warning("⚠️ 멀티에이전트 기능이 비활성화됩니다")
    multi_agent_service = None

# 데이터베이스 서비스 초기화 (Supabase)
try:
    db_service = DatabaseService()
    logger.info("✅ 데이터베이스 서비스 초기화 성공")
except Exception as e:
    logger.warning(f"⚠️ 데이터베이스 서비스 초기화 실패: {e}")
    logger.warning("⚠️ DB 없이 계속 실행합니다 (메모리 모드)")
    db_service = None

logger.info("✅ 서비스 초기화 완료")


@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    logger.info("📍 루트 엔드포인트 호출")

    # 서비스 타입 확인
    service_type = "yt-dlp (cookie)" if isinstance(youtube_service, YouTubeServiceYtDlp) else "youtube-transcript-api"

    response = {
        "message": "YouTube Summarizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "service_type": service_type,
        "cookie_auth": isinstance(youtube_service, YouTubeServiceYtDlp),
        "tailscale_ip": "100.118.223.116"
    }
    logger.debug("📤 루트 응답", extra={"data": response})
    return response


@app.get("/api/auth/cookie/status")
async def get_cookie_status():
    """쿠키 인증 상태 확인"""
    logger.info("🍪 쿠키 상태 확인 요청")

    try:
        if isinstance(youtube_service, YouTubeServiceYtDlp):
            cookie_method = youtube_service._get_cookie_method_name()
            return {
                "status": "active",
                "method": cookie_method,
                "message": "쿠키 인증 활성화됨",
                "can_access_membership": True,
                "tips": [
                    "Chrome이 완전히 종료되어 있어야 합니다",
                    "Chrome 바로가기에 --disable-features=LockProfileCookieDatabase 추가하면 편합니다",
                    "YouTube에 로그인되어 있어야 합니다"
                ]
            }
        else:
            return {
                "status": "inactive",
                "method": "none",
                "message": "기본 서비스 사용 중 (멤버십 영상 불가)",
                "can_access_membership": False
            }
    except Exception as e:
        logger.error(f"❌ 쿠키 상태 조회 실패", extra={"data": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/summarize", response_model=MultiAgentAnalyzeResponse)
async def summarize_video(request: SummarizeRequest):
    """
    유튜브 영상 URL을 받아 멀티에이전트 시스템으로 고급 분석을 수행합니다.

    Args:
        request: 유튜브 URL이 포함된 요청 객체

    Returns:
        MultiAgentAnalyzeResponse: 상세한 분석 결과와 종합 보고서

    Raises:
        400: 잘못된 URL 또는 자막 없음
        500: 서버 내부 오류
        503: 멀티에이전트 서비스 사용 불가
    """
    # 요청 정보 상세 로깅 (FCM 토큰 포함)
    fcm_token = request.fcm_token  # 직접 접근
    logger.info("📥 고급 분석 요청 수신", extra={"data": {
        "url": request.url,
        "user_id": request.user_id,
        "user_id_type": type(request.user_id).__name__,
        "has_fcm_token": bool(fcm_token),
        "fcm_token_preview": fcm_token[:20] + "..." if fcm_token else None,
        "fcm_token_length": len(fcm_token) if fcm_token else 0,
        "request_fields": list(request.__dict__.keys()),
        "request_data": request.model_dump(),  # 전체 요청 데이터
        "endpoint": "/api/summarize",
        "client_ip": "unknown",  # FastAPI에서 클라이언트 IP 가져오려면 별도 로직 필요
        "timestamp": datetime.now().isoformat()
    }})
    # 멀티에이전트 서비스 사용 가능 여부 확인
    if multi_agent_service is None:
        logger.error("❌ 멀티에이전트 서비스 사용 불가")
        raise HTTPException(
            status_code=503,
            detail="멀티에이전트 분석 서비스를 사용할 수 없습니다. 관리자에게 문의하세요."
        )
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        # 요청 데이터 로깅 (전문)
        logger.info("📥 고급 분석 요청 수신", extra={"data": {
            "url": request.url,
            "endpoint": "/api/summarize"
        }})
        
        # 0. 비디오 ID 추출 (캐시 확인용)
        video_id = youtube_service.extract_video_id(request.url)
        logger.info(f"🔍 비디오 ID 추출: {video_id}")
        
        # 1. DB에서 멀티에이전트 캐시된 데이터 확인 (추후 구현)
        # TODO: 멀티에이전트 전용 캐시 테이블 구현 필요
        
        # 2. 유튜브 영상 정보 및 자막 추출
        logger.info(f"🎬 유튜브 데이터 추출 시작: {request.url}")
        video_data = await youtube_service.get_video_data(request.url)
        
        # 비디오 데이터 로깅 (전문)
        logger.debug("📊 비디오 데이터 추출 완료", extra={"data": {
            "video_id": video_data.video_id,
            "title": video_data.title,
            "channel": video_data.channel,
            "duration": video_data.duration,
            "language": video_data.language,
            "transcript_length": len(video_data.transcript) if video_data.transcript else 0
        }})
        
        # 자막이 없는 경우 에러 처리
        if not video_data.transcript:
            logger.warning("⚠️ 자막 없음", extra={"data": {"video_id": video_data.video_id}})
            raise HTTPException(
                status_code=400,
                detail="자막을 찾을 수 없습니다. 다른 영상을 시도해주세요."
            )
        
        # 3. 멀티에이전트 시스템으로 고급 분석 수행
        logger.info(f"🎭 멀티에이전트 분석 시작")
        multi_agent_result = await multi_agent_service.process_full_analysis(
            transcript=video_data.transcript,
            title=video_data.title,
            video_id=video_data.video_id,
            language=video_data.language
        )
        
        # 분석 결과 로깅
        logger.debug("🎯 멀티에이전트 분석 완료", extra={"data": {
            "status": multi_agent_result.processing_status.status,
            "successful_agents": multi_agent_result.successful_agents,
            "total_agents": multi_agent_result.total_agents,
            "processing_time": multi_agent_result.processing_status.total_processing_time
        }})
        
        # 4. 응답 생성
        processing_time = asyncio.get_event_loop().time() - start_time
        
        # 최종 보고서 추출
        final_report = None
        if (multi_agent_result.report_synthesis and 
            hasattr(multi_agent_result.report_synthesis, 'get')):
            final_report = multi_agent_result.report_synthesis.get("final_report")
        
        response = MultiAgentAnalyzeResponse(
            video_id=video_data.video_id,
            title=video_data.title,
            channel=video_data.channel,
            duration=video_data.duration,
            language=video_data.language,
            analysis_result=multi_agent_result.model_dump(),
            final_report=final_report,
            transcript_available=True,
            analysis_type="multi_agent",
            processing_time=processing_time
        )
        
        # 5. DB에 저장 (백그라운드) - 멀티에이전트 결과용
        logger.info("🗄️ DB 저장 시도", extra={"data": {
            "has_db_service": db_service is not None,
            "user_id": request.user_id,
            "user_id_type": type(request.user_id).__name__,
            "user_id_length": len(request.user_id) if request.user_id else 0,
            "user_id_is_none": request.user_id is None,
            "user_id_is_empty": request.user_id == "" if request.user_id else True
        }})

        if db_service and request.user_id and request.user_id.strip():  # 빈 문자열도 체크
            try:
                logger.info("🔄 멀티에이전트 보고서 저장 시작", extra={"data": {
                    "user_id": request.user_id,
                    "video_id": video_data.video_id,
                    "title": video_data.title
                }})

                # 멀티에이전트 결과를 DB에 저장
                report_id = await db_service.save_multi_agent_report(
                    user_id=request.user_id,
                    video_id=video_data.video_id,
                    title=video_data.title,
                    channel=video_data.channel,
                    duration=video_data.duration,
                    language=video_data.language,
                    final_report=final_report,
                    agent_results={
                        "transcript_refinement": multi_agent_result.transcript_refinement,
                        "speaker_diarization": multi_agent_result.speaker_diarization,
                        "topic_cohesion": multi_agent_result.topic_cohesion,
                        "structure_design": multi_agent_result.structure_design,
                        "report_synthesis": multi_agent_result.report_synthesis
                    },
                    processing_status={
                        "status": multi_agent_result.processing_status.status,
                        "total_processing_time": multi_agent_result.processing_status.total_processing_time,
                        "successful_agents": multi_agent_result.successful_agents,
                        "total_agents": multi_agent_result.total_agents
                    }
                )

                if report_id:
                    logger.info(f"✅ 멀티에이전트 결과 DB 저장 완료", extra={"data": {
                        "report_id": report_id,
                        "video_id": video_data.video_id
                    }})
                else:
                    logger.warning("⚠️ 멀티에이전트 결과 DB 저장 실패")
            except Exception as e:
                logger.error(f"❌ DB 저장 중 오류", extra={"data": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": request.user_id,
                    "video_id": video_data.video_id,
                    "has_agent_results": len(multi_agent_result.model_dump()) > 0,
                    "processing_status": multi_agent_result.processing_status.status
                }})
        else:
            logger.info("⏭️ DB 저장 건너뜀", extra={"data": {
                "reason": "no_db_service" if not db_service else "no_user_id",
                "has_db_service": db_service is not None,
                "user_id_provided": request.user_id is not None,
                "user_id_value": request.user_id if request.user_id else "None"
            }})

        logger.info(f"✅ 고급 분석 완료: {video_data.video_id}", extra={"data": {
            "processing_time": f"{processing_time:.2f}초",
            "status": multi_agent_result.processing_status.status,
            "successful_agents": multi_agent_result.successful_agents
        }})

        # FCM 푸시 알림 전송 (옵셔널 - 실패해도 응답에 영향 없음)
        fcm_token = request.fcm_token  # getattr 대신 직접 접근
        logger.info("🔍 FCM 토큰 확인", extra={"data": {
            "has_fcm_token": bool(fcm_token),
            "fcm_token_preview": fcm_token[:20] + "..." if fcm_token else None,
            "fcm_token_length": len(fcm_token) if fcm_token else 0,
            "fcm_service_available": fcm_service.is_available(),
            "fcm_token_full": fcm_token  # 디버깅용 전체 토큰
        }})

        if fcm_token:
            try:
                logger.info("📱 FCM 푸시 알림 전송 시도", extra={"data": {
                    "fcm_token": fcm_token[:30] + "..." if len(fcm_token) > 30 else fcm_token,
                    "video_title": video_data.title,
                    "video_id": video_data.video_id
                }})

                result = await fcm_service.send_analysis_complete_notification(
                    fcm_token=fcm_token,
                    video_title=video_data.title,
                    video_id=video_data.video_id
                )

                logger.info("📱 FCM 전송 결과", extra={"data": {
                    "success": result,
                    "fcm_token_used": fcm_token[:20] + "..."
                }})
            except Exception as fcm_error:
                # FCM 전송 실패해도 분석 결과는 정상 반환
                logger.warning("⚠️ FCM 전송 실패 (무시하고 계속)", extra={"data": {
                    "error": str(fcm_error),
                    "error_type": type(fcm_error).__name__,
                    "fcm_token_tried": fcm_token[:20] + "..."
                }})
        else:
            logger.info("🔕 FCM 전송 건너뜀", extra={"data": {
                "reason": "no_fcm_token",
                "request_fields": list(request.__dict__.keys())
            }})

        return response
        
    except HTTPException as e:
        logger.error(f"❌ HTTP 예외 발생", extra={"data": {"status": e.status_code, "detail": e.detail}})
        raise
    except ValueError as e:
        logger.error(f"❌ 값 오류 발생", extra={"data": str(e)})
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        processing_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"❌ 예상치 못한 오류", extra={"data": {
            "error": str(e),
            "error_type": type(e).__name__,
            "elapsed_time": f"{processing_time:.2f}초"
        }})
        raise HTTPException(
            status_code=500, 
            detail=f"고급 분석 중 오류가 발생했습니다: {str(e)}"
        )



@app.get("/api/health")
async def health_check():
    """
    서버 상태 확인 엔드포인트

    Returns:
        dict: 서버 상태 정보
    """
    logger.info("🏥 헬스체크 요청 수신")

    try:
        # 각 서비스 상태 체크
        db_status = "connected" if user_service and db_service else "disconnected"
        yt_status = "ready" if youtube_service else "not_ready"
        ai_status = "ready" if summarizer_service else "not_ready"
        multi_agent_status = "ready" if multi_agent_service else "not_ready"

        health_data = {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_status,
                "youtube": yt_status,
                "ai": ai_status,
                "multi_agent": multi_agent_status
            }
        }

        logger.info("✅ 헬스체크 성공", extra={"data": health_data})

        return health_data

    except Exception as e:
        error_data = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        logger.error("❌ 헬스체크 실패", extra={"data": error_data})

        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content=error_data
        )


@app.get("/api/auth/check/{nickname}")
async def check_nickname(nickname: str):
    """
    닉네임 중복 확인 (대소문자 무시)
    
    Args:
        nickname: 확인할 닉네임
    
    Returns:
        중복 여부와 메시지
    """
    logger.info(f"📥 닉네임 중복 확인 요청: {nickname}")
    
    try:
        result = await user_service.check_nickname(nickname)
        logger.info(f"✅ 닉네임 확인 완료", extra={"data": result})
        return result
    except Exception as e:
        logger.error(f"❌ 닉네임 확인 실패", extra={"data": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/nickname", response_model=NicknameLoginResponse)
async def login_with_nickname(request: NicknameLoginRequest):
    """
    닉네임으로 로그인 또는 등록
    
    Args:
        request: 닉네임 정보
    
    Returns:
        사용자 정보와 신규 여부
    """
    logger.info(f"📥 닉네임 로그인/등록 요청", extra={"data": {"nickname": request.nickname}})
    
    try:
        result = await user_service.login_or_register(request.nickname)
        logger.info(f"✅ 로그인/등록 성공", extra={"data": {
            "id": result["id"],
            "nickname": result["nickname"],
            "isNew": result["isNew"]
        }})
        return NicknameLoginResponse(**result)
    except Exception as e:
        logger.error(f"❌ 로그인/등록 실패", extra={"data": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/{report_id}")
async def get_report_detail(report_id: str):
    """
    보고서 상세 조회 (에이전트 결과 포함)

    Args:
        report_id: 보고서 ID

    Returns:
        보고서 상세 정보와 에이전트별 결과
    """
    logger.info(f"📥 보고서 상세 조회 요청", extra={"data": {"report_id": report_id}})

    try:
        if db_service:
            # 데이터베이스에서 보고서와 에이전트 결과 조회
            report = await db_service.get_report_with_agents(report_id=report_id)

            if report:
                logger.info(f"✅ 보고서 상세 조회 완료", extra={"data": {
                    "report_id": report_id,
                    "video_id": report.get("video_id"),
                    "agent_count": len(report.get("agent_results", {}))
                }})
                return report
            else:
                logger.warning(f"⚠️ 보고서 없음: {report_id}")
                raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다")
        else:
            logger.warning("⚠️ 데이터베이스 서비스 사용 불가")
            raise HTTPException(status_code=503, detail="데이터베이스 서비스를 사용할 수 없습니다")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 보고서 상세 조회 실패", extra={"data": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/user/{user_id}")
async def get_user_reports(user_id: str):
    """
    사용자별 분석 보고서 목록 조회

    Args:
        user_id: 사용자 ID

    Returns:
        사용자의 분석 보고서 목록
    """
    logger.info(f"📥 사용자 보고서 목록 조회 요청", extra={"data": {"user_id": user_id}})

    try:
        if db_service:
            # 데이터베이스에서 사용자별 보고서 조회
            reports = await db_service.get_user_reports(user_id=user_id, limit=20)

            logger.info(f"✅ 보고서 목록 조회 완료", extra={"data": {
                "user_id": user_id,
                "count": len(reports)
            }})

            return {"reports": reports}
        else:
            logger.warning("⚠️ 데이터베이스 서비스 사용 불가")
            return {"reports": []}
    except Exception as e:
        logger.error(f"❌ 보고서 목록 조회 실패", extra={"data": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/summaries")
async def get_summaries(user_id: Optional[str] = None):
    """
    요약 목록 조회 (프론트엔드 호환용)

    Args:
        user_id: 사용자 ID (쿼리 파라미터)

    Returns:
        사용자의 요약 목록 (배열 형태로 반환)
    """
    logger.info(f"📥 요약 목록 조회 요청", extra={"data": {"user_id": user_id}})

    try:
        if not user_id:
            # user_id가 없으면 빈 배열 반환
            logger.info("📋 user_id 없음, 빈 목록 반환")
            return []

        if db_service:
            # 데이터베이스에서 사용자별 보고서 조회
            reports = await db_service.get_user_reports(user_id=user_id, limit=20)

            # 프론트엔드 호환 형식으로 변환
            summaries = []
            for report in reports:
                # final_report에서 한 줄 요약 추출 시도
                final_report = report.get("final_report", "")
                one_line_summary = ""
                if final_report:
                    # 첫 번째 문장이나 첫 줄을 한 줄 요약으로 사용
                    lines = final_report.split('\n')
                    for line in lines:
                        if line.strip() and not line.startswith('#'):
                            one_line_summary = line.strip()[:200]  # 최대 200자
                            break

                summary = {
                    "video_id": report.get("video_id"),
                    "url": f"https://youtube.com/watch?v={report.get('video_id')}",
                    "title": report.get("title"),
                    "channel": report.get("channel", ""),  # channel_title -> channel
                    "channel_title": report.get("channel", ""),  # 호환성 유지
                    "duration": report.get("duration", ""),
                    "thumbnail_url": f"https://i.ytimg.com/vi/{report.get('video_id')}/maxresdefault.jpg",
                    "published_at": report.get("created_at"),
                    "view_count": 0,  # 백엔드에서 제공하지 않음
                    "summary": final_report,  # 전체 보고서
                    "one_line": one_line_summary,  # 한 줄 요약
                    "one_line_summary": one_line_summary,  # 호환성
                    "key_points": [],  # 빈 배열로 초기화
                    "detailed_summary": final_report,  # 상세 요약
                    "created_at": report.get("created_at"),
                    "multi_agent": True,  # 멀티에이전트 결과임을 표시
                    "report_id": report.get("id"),  # 보고서 ID 추가
                    "id": report.get("id")  # id 필드 추가
                }
                summaries.append(summary)

            logger.info(f"✅ 요약 목록 조회 완료", extra={"data": {
                "user_id": user_id,
                "count": len(summaries)
            }})

            return summaries  # 배열로 직접 반환
        else:
            logger.warning("⚠️ 데이터베이스 서비스 사용 불가")
            return []
    except Exception as e:
        logger.error(f"❌ 요약 목록 조회 실패", extra={"data": {"error": str(e)}})
        return []  # 에러 시에도 빈 배열 반환


@app.get("/health")
async def health_check():
    """서버 상태 확인 엔드포인트"""
    logger.debug("🏥 헬스 체크 호출")
    return {"status": "healthy", "service": "youtube-summarizer"}


@app.get("/api/cookies/status")
async def cookie_status():
    """쿠키 상태 확인 엔드포인트"""
    from app.services.cookie_refresher import get_cookie_refresher

    cookie_refresher = get_cookie_refresher()
    status = cookie_refresher.get_status()

    logger.info("🍪 쿠키 상태 조회", extra={"data": status})
    return status


@app.post("/api/cookies/refresh")
async def refresh_cookies():
    """수동 쿠키 갱신 엔드포인트"""
    from app.services.cookie_refresher import get_cookie_refresher

    cookie_refresher = get_cookie_refresher()
    success = cookie_refresher.refresh_cookies()

    if success:
        logger.info("✅ 쿠키 수동 갱신 성공")
        return {"status": "success", "message": "쿠키가 갱신되었습니다"}
    else:
        logger.error("❌ 쿠키 수동 갱신 실패")
        raise HTTPException(status_code=500, detail="쿠키 갱신 실패")


# 테스트용 조회 API
@app.get("/api/test/reports")
async def get_all_reports():
    """
    테스트용: 모든 분석 보고서 조회
    - 데이터베이스에 저장된 모든 보고서를 조회합니다
    - user_id와 nickname 정보도 함께 반환합니다
    """
    try:
        logger.info("📊 전체 보고서 조회 시작")

        # 보고서와 닉네임 정보를 조인하여 조회
        response = db_service.client.table("analysis_reports")\
            .select("*, nicknames!left(id, nickname)")\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()

        if response.data:
            logger.info(f"✅ {len(response.data)}개 보고서 조회 성공")
            for report in response.data:
                # nicknames 정보 처리
                if report.get('nicknames'):
                    report['user_nickname'] = report['nicknames'].get('nickname')
                    del report['nicknames']
                else:
                    report['user_nickname'] = None

            return {
                "status": "success",
                "count": len(response.data),
                "reports": response.data
            }
        else:
            logger.info("ℹ️ 저장된 보고서 없음")
            return {
                "status": "success",
                "count": 0,
                "reports": []
            }

    except Exception as e:
        logger.error(f"❌ 보고서 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보고서 조회 실패: {str(e)}")


@app.get("/api/test/reports/{video_id}")
async def get_report_by_video(video_id: str):
    """
    테스트용: 특정 비디오의 분석 보고서 조회
    - video_id로 보고서를 조회합니다
    - user_id와 nickname 정보도 함께 반환합니다
    """
    try:
        logger.info(f"📊 비디오별 보고서 조회: {video_id}")

        response = db_service.client.table("analysis_reports")\
            .select("*, nicknames!left(id, nickname)")\
            .eq("video_id", video_id)\
            .execute()

        if response.data:
            logger.info(f"✅ {len(response.data)}개 보고서 발견")
            for report in response.data:
                # nicknames 정보 처리
                if report.get('nicknames'):
                    report['user_nickname'] = report['nicknames'].get('nickname')
                    del report['nicknames']
                else:
                    report['user_nickname'] = None

            return {
                "status": "success",
                "video_id": video_id,
                "count": len(response.data),
                "reports": response.data
            }
        else:
            logger.info(f"ℹ️ {video_id}에 대한 보고서 없음")
            return {
                "status": "success",
                "video_id": video_id,
                "count": 0,
                "reports": []
            }

    except Exception as e:
        logger.error(f"❌ 보고서 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보고서 조회 실패: {str(e)}")


@app.post("/api/test/save-report")
async def test_save_report(
    user_id: str = "Rex",
    video_id: str = "test123",
    title: str = "테스트 비디오",
    channel: str = "테스트 채널"
):
    """
    테스트용: 보고서 저장 테스트
    - 닉네임을 UUID로 변환하여 저장하는 기능을 테스트합니다
    """
    try:
        logger.info(f"🧪 테스트 보고서 저장 시작: {user_id}")

        # 더미 에이전트 결과
        agent_results = {
            "transcript_refinement": {"success": True, "result": {"test": "data"}},
            "speaker_diarization": {"success": True, "result": {"test": "data"}},
            "topic_cohesion": {"success": True, "result": {"test": "data"}},
            "structure_design": {"success": True, "result": {"test": "data"}},
            "report_synthesis": {"success": True, "result": {"test": "data"}}
        }

        processing_status = {
            "total_processing_time": 1.23,
            "status": "completed"
        }

        # 보고서 저장
        report_id = await db_service.save_multi_agent_report(
            user_id=user_id,
            video_id=video_id,
            title=title,
            channel=channel,
            agent_results=agent_results,
            processing_status=processing_status
        )

        if report_id:
            logger.info(f"✅ 테스트 보고서 저장 성공: {report_id}")

            # 저장된 보고서 조회
            saved_report = db_service.client.table("analysis_reports")\
                .select("*, nicknames!left(id, nickname)")\
                .eq("id", report_id)\
                .single()\
                .execute()

            if saved_report.data:
                if saved_report.data.get('nicknames'):
                    saved_report.data['user_nickname'] = saved_report.data['nicknames'].get('nickname')
                    del saved_report.data['nicknames']

            return {
                "status": "success",
                "report_id": report_id,
                "message": f"보고서가 성공적으로 저장되었습니다 (user: {user_id})",
                "saved_report": saved_report.data
            }
        else:
            raise HTTPException(status_code=500, detail="보고서 저장 실패")

    except Exception as e:
        logger.error(f"❌ 테스트 보고서 저장 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테스트 실패: {str(e)}")


# Swagger UI는 /docs에서 자동으로 제공됨
# ReDoc은 /redoc에서 자동으로 제공됨