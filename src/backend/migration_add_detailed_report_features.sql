-- DB 마이그레이션: 리포트 상세 분석 기능 추가
-- 생성일: 2025-01-11
-- 목적: 면접 리포트에 AI 총평, 기술 분석, 개선 플랜 기능 추가

-- 1. interview_reports 테이블에 새로운 컬럼들 추가
ALTER TABLE interview_reports 
ADD COLUMN overall_summary TEXT,
ADD COLUMN interview_readiness_score INTEGER,
ADD COLUMN key_talking_points JSON;

-- 2. 프로젝트 기술 분석 테이블 생성
CREATE TABLE IF NOT EXISTS project_technical_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES interview_reports(id) ON DELETE CASCADE,
    architecture_understanding INTEGER CHECK (architecture_understanding >= 0 AND architecture_understanding <= 100),
    code_quality_awareness INTEGER CHECK (code_quality_awareness >= 0 AND code_quality_awareness <= 100),
    problem_solving_approach TEXT,
    technology_depth TEXT,
    project_complexity_handling TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 면접 개선 액션 플랜 테이블 생성
CREATE TABLE IF NOT EXISTS interview_improvement_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES interview_reports(id) ON DELETE CASCADE,
    immediate_actions JSON,
    study_recommendations JSON,
    practice_scenarios JSON,
    weak_areas JSON,
    preparation_timeline TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

-- 6. 테이블 코멘트 추가
COMMENT ON TABLE project_technical_analysis IS '프로젝트 기술 분석 - 면접자의 기술적 이해도 평가';
COMMENT ON TABLE interview_improvement_plans IS '면접 개선 액션 플랜 - 구체적인 면접 준비 가이드';

COMMENT ON COLUMN interview_reports.overall_summary IS 'AI가 생성한 면접 총평 (200-300자)';
COMMENT ON COLUMN interview_reports.interview_readiness_score IS '면접 준비도 점수 (0-100, 실제 면접 대비 준비 수준)';
COMMENT ON COLUMN interview_reports.key_talking_points IS '면접에서 강조할 핵심 포인트들 (JSON 배열)';

COMMENT ON COLUMN project_technical_analysis.architecture_understanding IS '아키텍처 이해도 점수 (0-100)';
COMMENT ON COLUMN project_technical_analysis.code_quality_awareness IS '코드 품질 인식 점수 (0-100)';

-- 마이그레이션 완료 로그
INSERT INTO migration_log (migration_name, executed_at, description) 
VALUES (
    'add_detailed_report_features_v1', 
    NOW(), 
    '면접 리포트 상세 분석 기능 추가: AI 총평, 기술 분석, 개선 플랜'
) ON CONFLICT DO NOTHING;