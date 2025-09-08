#!/bin/bash

# 백엔드 환경 설정 스크립트

echo "🚀 YouTube Summarizer Backend 환경 설정 시작..."

# 가상환경 생성
echo "📦 가상환경 생성 중..."
python3 -m venv venv

# 가상환경 활성화
echo "✅ 가상환경 활성화..."
source venv/bin/activate

# pip 업그레이드
echo "📈 pip 업그레이드..."
pip install --upgrade pip

# 패키지 설치
echo "📚 필요 패키지 설치 중..."
pip install -r requirements.txt

# .env 파일 생성 (없는 경우)
if [ ! -f .env ]; then
    echo "🔧 .env 파일 생성..."
    cp .env.example .env
    echo "⚠️  .env 파일에 OPENAI_API_KEY를 설정해주세요!"
fi

echo "✨ 환경 설정 완료!"
echo ""
echo "실행 방법:"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
echo "API 문서:"
echo "  http://localhost:8000/docs"