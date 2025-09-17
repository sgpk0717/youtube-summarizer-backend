-- YouTube Summarizer DB 스키마 업데이트 및 마이그레이션 (수정본)
-- Supabase에서 실행해주세요

-- 1. 닉네임 테이블 생성
CREATE TABLE IF NOT EXISTS nicknames (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nickname VARCHAR(50) NOT NULL,
    nickname_lower VARCHAR(50) GENERATED ALWAYS AS (LOWER(nickname)) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_nickname_lower UNIQUE (nickname_lower)
);

-- 닉네임 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_nicknames_lower ON nicknames(nickname_lower);

-- 2. 기존 보고서 테이블에 user_id 컬럼 추가 (없으면 테이블 생성)
CREATE TABLE IF NOT EXISTS analysis_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    channel TEXT NOT NULL,
    duration VARCHAR(50),
    language VARCHAR(10),
    analysis_result JSONB,
    final_report TEXT,
    transcript_available BOOLEAN DEFAULT true,
    analysis_type VARCHAR(50) DEFAULT 'multi_agent',
    processing_time FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- user_id 컬럼 추가 (이미 있으면 무시)
ALTER TABLE analysis_reports 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES nicknames(id);

-- user_id 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON analysis_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_video_id ON analysis_reports(video_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON analysis_reports(created_at DESC);

-- 3. Rex 사용자 생성 및 기존 데이터 마이그레이션
DO $$
DECLARE
    rex_user_id UUID;
BEGIN
    -- Rex 사용자가 이미 있는지 확인
    SELECT id INTO rex_user_id 
    FROM nicknames 
    WHERE nickname_lower = 'rex' 
    LIMIT 1;
    
    -- Rex 사용자가 없으면 생성
    IF rex_user_id IS NULL THEN
        INSERT INTO nicknames (nickname) 
        VALUES ('Rex') 
        RETURNING id INTO rex_user_id;
        
        RAISE NOTICE 'Rex 사용자 생성됨: %', rex_user_id;
    ELSE
        RAISE NOTICE 'Rex 사용자 이미 존재: %', rex_user_id;
    END IF;
    
    -- 기존 보고서 중 user_id가 NULL인 것들을 Rex로 업데이트
    UPDATE analysis_reports 
    SET user_id = rex_user_id 
    WHERE user_id IS NULL;
    
    RAISE NOTICE '마이그레이션 완료: % 개의 보고서가 Rex 사용자로 할당됨', 
        (SELECT COUNT(*) FROM analysis_reports WHERE user_id = rex_user_id);
END $$;

-- 4. 보고서 조회를 위한 뷰 생성 (선택사항)
CREATE OR REPLACE VIEW user_reports_view AS
SELECT 
    r.*,
    n.nickname as user_nickname
FROM analysis_reports r
LEFT JOIN nicknames n ON r.user_id = n.id
ORDER BY r.created_at DESC;

-- 5. 통계 확인
SELECT 
    'nicknames 테이블' as table_name,
    COUNT(*) as total_count
FROM nicknames
UNION ALL
SELECT 
    'analysis_reports 테이블',
    COUNT(*)
FROM analysis_reports
UNION ALL
SELECT 
    'Rex의 보고서',
    COUNT(*)
FROM analysis_reports r
JOIN nicknames n ON r.user_id = n.id
WHERE n.nickname_lower = 'rex';

-- 실행 완료 메시지
SELECT '✅ DB 스키마 업데이트 및 마이그레이션 완료!' as status;