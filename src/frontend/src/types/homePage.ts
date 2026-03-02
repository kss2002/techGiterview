/**
 * HomePage 관련 타입 정의
 */

export interface HomePageState {
  repoUrl: string;
  isAnalyzing: boolean;
  showApiKeySetup: boolean;
}

export interface AnalysisRequest {
  repo_url: string;
}

export interface AnalysisResponse {
  success?: boolean;
  data?: {
    success?: boolean;
    analysis_id?: string;
    error?: string;
  };
  analysis_id?: string;
  error?: string;
}
