-- Migration: Add AI generation status tracking columns
-- Purpose: Track whether analysis data is from real AI or fallback data
-- Date: 2024-11-XX

-- Add is_ai_generated column to interview_reports table
ALTER TABLE interview_reports 
ADD COLUMN is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE;

-- Add is_ai_generated column to project_technical_analysis table
ALTER TABLE project_technical_analysis 
ADD COLUMN is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE;

-- Add is_ai_generated column to interview_improvement_plans table
ALTER TABLE interview_improvement_plans 
ADD COLUMN is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE;

-- Update existing records to mark them as non-AI generated (since they might be fallback data)
UPDATE interview_reports SET is_ai_generated = FALSE;
UPDATE project_technical_analysis SET is_ai_generated = FALSE;
UPDATE interview_improvement_plans SET is_ai_generated = FALSE;

-- Create index for better query performance
CREATE INDEX idx_interview_reports_ai_generated ON interview_reports(is_ai_generated);
CREATE INDEX idx_technical_analysis_ai_generated ON project_technical_analysis(is_ai_generated);
CREATE INDEX idx_improvement_plans_ai_generated ON interview_improvement_plans(is_ai_generated);