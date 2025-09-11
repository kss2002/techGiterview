-- SQLite용 DB 마이그레이션: 리포트 상세 분석 기능 추가
-- 생성일: 2025-01-11
-- 목적: 면접 리포트에 AI 총평, 기술 분석, 개선 플랜 기능 추가

-- 1. interview_reports 테이블에 새로운 컬럼들 추가
ALTER TABLE interview_reports ADD COLUMN overall_summary TEXT;
ALTER TABLE interview_reports ADD COLUMN interview_readiness_score INTEGER;
ALTER TABLE interview_reports ADD COLUMN key_talking_points TEXT; -- SQLite는 JSON을 TEXT로 저장

-- 2. 프로젝트 기술 분석 테이블 생성
CREATE TABLE IF NOT EXISTS project_technical_analysis (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL REFERENCES interview_reports(id) ON DELETE CASCADE,
    architecture_understanding INTEGER CHECK (architecture_understanding >= 0 AND architecture_understanding <= 100),
    code_quality_awareness INTEGER CHECK (code_quality_awareness >= 0 AND code_quality_awareness <= 100),
    problem_solving_approach TEXT,
    technology_depth TEXT,
    project_complexity_handling TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 면접 개선 액션 플랜 테이블 생성
CREATE TABLE IF NOT EXISTS interview_improvement_plans (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL REFERENCES interview_reports(id) ON DELETE CASCADE,
    immediate_actions TEXT, -- JSON as TEXT
    study_recommendations TEXT, -- JSON as TEXT
    practice_scenarios TEXT, -- JSON as TEXT
    weak_areas TEXT, -- JSON as TEXT
    preparation_timeline TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 인덱스 추가 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_project_technical_analysis_report_id ON project_technical_analysis(report_id);
CREATE INDEX IF NOT EXISTS idx_interview_improvement_plans_report_id ON interview_improvement_plans(report_id);
CREATE INDEX IF NOT EXISTS idx_interview_reports_readiness_score ON interview_reports(interview_readiness_score);

-- 5. 기존 데이터에 대한 기본값 설정 (선택사항)
UPDATE interview_reports 
SET interview_readiness_score = CASE 
    WHEN overall_score >= 8.0 THEN 85
    WHEN overall_score >= 6.0 THEN 70
    WHEN overall_score >= 4.0 THEN 55
    ELSE 40
END
WHERE interview_readiness_score IS NULL;