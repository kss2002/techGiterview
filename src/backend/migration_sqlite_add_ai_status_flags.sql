-- SQLite Migration: Add AI generation status tracking columns
-- Purpose: Track whether analysis data is from real AI or fallback data
-- Date: 2024-11-XX
-- Note: SQLite version for local development

-- Add is_ai_generated column to interview_reports table
ALTER TABLE interview_reports 
ADD COLUMN is_ai_generated INTEGER NOT NULL DEFAULT 0;

-- Add is_ai_generated column to project_technical_analysis table
ALTER TABLE project_technical_analysis 
ADD COLUMN is_ai_generated INTEGER NOT NULL DEFAULT 0;

-- Add is_ai_generated column to interview_improvement_plans table
ALTER TABLE interview_improvement_plans 
ADD COLUMN is_ai_generated INTEGER NOT NULL DEFAULT 0;

-- Update existing records to mark them as non-AI generated (since they might be fallback data)
UPDATE interview_reports SET is_ai_generated = 0;
UPDATE project_technical_analysis SET is_ai_generated = 0;
UPDATE interview_improvement_plans SET is_ai_generated = 0;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_interview_reports_ai_generated ON interview_reports(is_ai_generated);
CREATE INDEX IF NOT EXISTS idx_technical_analysis_ai_generated ON project_technical_analysis(is_ai_generated);
CREATE INDEX IF NOT EXISTS idx_improvement_plans_ai_generated ON interview_improvement_plans(is_ai_generated);