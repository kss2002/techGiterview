import { GITHUB_URL_PATTERN } from '../constants/sampleRepos';

/**
 * GitHub URL 유효성 검사
 */
export const validateGitHubUrl = (url: string): boolean => {
  return GITHUB_URL_PATTERN.test(url);
};

/**
 * 분석 응답 처리
 */
export const processAnalysisResponse = (
  result: any
): { analysisId?: string; error?: string } => {
  let analysisData = result;
  if (result.data) {
    analysisData = result.data;
  }

  if (result.success || analysisData.success) {
    if (analysisData.analysis_id) {
      return { analysisId: analysisData.analysis_id };
    } else {
      return { error: '분석 ID를 받지 못했습니다.' };
    }
  } else {
    return {
      error: analysisData.error || result.error || '분석에 실패했습니다.',
    };
  }
};

/**
 * 에러 메시지 처리 및 API 키 설정 필요 여부 확인
 */
export const processError = (
  error: unknown
): {
  message: string;
  shouldShowApiKeySetup: boolean;
} => {
  const errorMessage =
    error instanceof Error ? error.message : '오류가 발생했습니다.';
  const shouldShowApiKeySetup =
    errorMessage.includes('API 키') || errorMessage.includes('접근이 제한');

  return {
    message: errorMessage,
    shouldShowApiKeySetup,
  };
};

/**
 * 저장소 이름 추출 (owner/repo 형식)
 */
export const extractRepoName = (url: string): string => {
  try {
    return url.split('/').slice(-2).join('/');
  } catch {
    return url;
  }
};
