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
from app.services.summarizer_service import SummarizerService
from app.services.database_service import DatabaseService
from app.services.multi_agent_service import MultiAgentService
from app.models.summary import SummaryResponse, SummarizeRequest, MultiAgentAnalyzeRequest, MultiAgentAnalyzeResponse
from app.utils.logger import setup_logger, log_function_call

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
cors_origins = [os.getenv("FRONTEND_URL", "http://localhost:3000")]
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
youtube_service = YouTubeService()
summarizer_service = SummarizerService()

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
    response = {
        "message": "YouTube Summarizer API", 
        "version": "1.0.0",
        "docs": "/docs"
    }
    logger.debug("📤 루트 응답", extra={"data": response})
    return response


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
        # TODO: 멀티에이전트 결과 저장 로직 구현
        
        logger.info(f"✅ 고급 분석 완료: {video_data.video_id}", extra={"data": {
            "processing_time": f"{processing_time:.2f}초",
            "status": multi_agent_result.processing_status.status,
            "successful_agents": multi_agent_result.successful_agents
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




@app.get("/health")
async def health_check():
    """서버 상태 확인 엔드포인트"""
    logger.debug("🏥 헬스 체크 호출")
    return {"status": "healthy", "service": "youtube-summarizer"}


# Swagger UI는 /docs에서 자동으로 제공됨
# ReDoc은 /redoc에서 자동으로 제공됨