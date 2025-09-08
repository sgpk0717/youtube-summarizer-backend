"""
로그 시스템 모듈
상세한 로깅을 위한 커스텀 로거 설정
"""
import logging
import os
import json
from datetime import datetime
from pathlib import Path
import inspect
from typing import Any, Optional


class CustomFormatter(logging.Formatter):
    """커스텀 로그 포매터 - 상세한 정보 포함"""
    
    def format(self, record):
        # 타임스탬프 추가
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # 호출 위치 정보 추가
        caller_frame = inspect.currentframe()
        if caller_frame and caller_frame.f_back and caller_frame.f_back.f_back:
            frame = caller_frame.f_back.f_back
            filename = os.path.basename(frame.f_code.co_filename)
            function = frame.f_code.co_name
            line_no = frame.f_lineno
            location = f"{filename}:{function}:{line_no}"
        else:
            location = f"{record.filename}:{record.funcName}:{record.lineno}"
        
        # 기본 메시지 포맷
        formatted_message = f"[{timestamp}] [{record.levelname}] [{location}] - {record.getMessage()}"
        
        # 추가 데이터가 있으면 포함 (전문 로깅)
        if hasattr(record, 'data') and record.data:
            try:
                # 데이터 전문을 JSON 형식으로 포맷팅
                data_str = json.dumps(record.data, ensure_ascii=False, indent=2)
                formatted_message += f"\n📊 DATA: {data_str}"
            except:
                formatted_message += f"\n📊 DATA: {str(record.data)}"
        
        return formatted_message


def setup_logger(name: str = "youtube_summarizer") -> logging.Logger:
    """
    로거 설정 및 반환
    
    Args:
        name: 로거 이름
    
    Returns:
        설정된 로거 객체
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 있으면 중복 설정 방지
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # 로그 디렉토리 생성
    log_dir = Path("/Users/seonggukpark/youtube-summarizer/backend/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 파일명 생성 (날짜와 시간 포함)
    now = datetime.now()
    log_filename = now.strftime("%Y_%m_%d_%H.txt")
    log_path = log_dir / log_filename
    
    # 파일 핸들러 설정
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(CustomFormatter())
    
    # 콘솔 핸들러 설정 (개발 환경용)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CustomFormatter())
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


class LoggerMixin:
    """로깅 기능을 제공하는 믹스인 클래스"""
    
    @property
    def logger(self) -> logging.Logger:
        """로거 인스턴스 반환"""
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(self.__class__.__name__)
        return self._logger
    
    def log_debug(self, message: str, data: Optional[Any] = None):
        """디버그 로그 출력"""
        self._log_with_data(logging.DEBUG, message, data)
    
    def log_info(self, message: str, data: Optional[Any] = None):
        """정보 로그 출력"""
        self._log_with_data(logging.INFO, message, data)
    
    def log_warning(self, message: str, data: Optional[Any] = None):
        """경고 로그 출력"""
        self._log_with_data(logging.WARNING, message, data)
    
    def log_error(self, message: str, data: Optional[Any] = None):
        """에러 로그 출력"""
        self._log_with_data(logging.ERROR, message, data)
    
    def _log_with_data(self, level: int, message: str, data: Optional[Any] = None):
        """데이터와 함께 로그 출력"""
        # 호출 위치 정보 추가
        frame = inspect.currentframe()
        if frame and frame.f_back and frame.f_back.f_back:
            caller_frame = frame.f_back.f_back
            filename = os.path.basename(caller_frame.f_code.co_filename)
            function = caller_frame.f_code.co_name
            line_no = caller_frame.f_lineno
            
            # 로그 레코드 생성
            record = self.logger.makeRecord(
                self.logger.name,
                level,
                filename,
                line_no,
                message,
                args=(),
                exc_info=None,
                func=function
            )
            
            # 데이터 추가
            if data is not None:
                record.data = data
            else:
                record.data = None
            
            self.logger.handle(record)
        else:
            # 폴백: 일반 로깅
            if data:
                self.logger.log(level, f"{message} | DATA: {data}")
            else:
                self.logger.log(level, message)


# 글로벌 로거 인스턴스
logger = setup_logger("youtube_summarizer")


def log_function_call(func):
    """함수 호출을 로깅하는 데코레이터"""
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        module_name = func.__module__
        
        # 함수 시작 로그
        logger.info(f"🚀 함수 시작: {module_name}.{func_name}")
        
        # 인자 로깅 (전문)
        if args or kwargs:
            arg_data = {
                "args": str(args),
                "kwargs": str(kwargs)
            }
            logger.debug(f"📥 인자 전달: {func_name}", extra={"data": arg_data})
        
        try:
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 결과 로깅 (전문)
            logger.debug(f"📤 반환값: {func_name}", extra={"data": str(result)})
            logger.info(f"✅ 함수 완료: {module_name}.{func_name}")
            
            return result
            
        except Exception as e:
            # 에러 로깅
            logger.error(f"❌ 함수 에러: {module_name}.{func_name}", extra={"data": str(e)})
            raise
    
    return wrapper