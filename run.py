"""
FastAPI 서버 실행 스크립트
"""
import uvicorn
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

if __name__ == "__main__":
    # 서버 설정
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"Server starting: http://{host}:{port}")
    print(f"API Docs: http://localhost:{port}/docs")
    print(f"ReDoc: http://localhost:{port}/redoc")
    
    # 서버 실행
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,  # 개발 모드에서 자동 리로드
        log_level="info"
    )