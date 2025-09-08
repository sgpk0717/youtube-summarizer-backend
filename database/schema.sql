-- YouTube Summarizer Database Schema for Supabase
-- ================================================

-- 1. 비디오 메타데이터 및 자막 저장 테이블
CREATE TABLE IF NOT EXISTS videos (
    -- Primary Key
    video_id VARCHAR(20) PRIMARY KEY,  -- YouTube video ID (예: Lg0rXSsESbA)
    
    -- 메타데이터
    title TEXT NOT NULL,                -- 비디오 제목
    channel_name VARCHAR(255),          -- 채널명
    channel_url TEXT,                   -- 채널 URL
    thumbnail_url TEXT,                 -- 썸네일 URL
    duration VARCHAR(50),               -- 영상 길이 (예: "15:30" 또는 "Unknown")
    
    -- 자막 데이터
    transcript_text TEXT,               -- 풀텍스트 자막 (공백으로 연결된 전체 텍스트)
    transcript_json JSONB,              -- 타임스탬프별 자막 배열 [{text, start, duration}, ...]
    language_code VARCHAR(10),          -- 자막 언어 코드 (예: ko, en)
    is_auto_generated BOOLEAN,          -- 자동 생성 자막 여부
    
    -- 요약 데이터
    summary_brief TEXT,                 -- 한 줄 요약
    summary_key_points TEXT[],          -- 핵심 포인트 배열
    summary_detailed TEXT,              -- 상세 요약
    
    -- 메타데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1      -- 조회수
);

-- 2. 인덱스 생성
-- video_id는 이미 PRIMARY KEY이므로 자동으로 인덱스 생성됨
CREATE INDEX idx_videos_created_at ON videos(created_at DESC);
CREATE INDEX idx_videos_channel_name ON videos(channel_name);
CREATE INDEX idx_videos_language_code ON videos(language_code);

-- 3. 풀텍스트 검색을 위한 인덱스 (PostgreSQL의 Full Text Search 기능 활용)
CREATE INDEX idx_videos_transcript_fulltext ON videos 
    USING gin(to_tsvector('simple', transcript_text));

-- 4. 업데이트 시간 자동 갱신을 위한 트리거
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_videos_updated_at 
    BEFORE UPDATE ON videos 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 5. RLS (Row Level Security) 정책 설정 (Supabase 특화)
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기 가능
CREATE POLICY "Videos are viewable by everyone" 
    ON videos FOR SELECT 
    USING (true);

-- 인증된 사용자만 삽입 가능 (필요시 수정)
CREATE POLICY "Anyone can insert videos" 
    ON videos FOR INSERT 
    WITH CHECK (true);

-- 인증된 사용자만 업데이트 가능 (필요시 수정)
CREATE POLICY "Anyone can update videos" 
    ON videos FOR UPDATE 
    USING (true);

-- 6. 통계/분석용 뷰 (선택사항)
CREATE VIEW popular_videos AS
SELECT 
    video_id,
    title,
    channel_name,
    language_code,
    access_count,
    created_at
FROM videos
WHERE access_count > 1
ORDER BY access_count DESC, created_at DESC;

-- 7. 저장 프로시저: 비디오 조회 시 access_count 증가 및 last_accessed_at 업데이트
CREATE OR REPLACE FUNCTION increment_video_access(p_video_id VARCHAR)
RETURNS void AS $$
BEGIN
    UPDATE videos 
    SET 
        access_count = access_count + 1,
        last_accessed_at = CURRENT_TIMESTAMP
    WHERE video_id = p_video_id;
END;
$$ LANGUAGE plpgsql;

-- 사용 예시:
-- SELECT * FROM videos WHERE video_id = 'Lg0rXSsESbA';
-- SELECT increment_video_access('Lg0rXSsESbA');