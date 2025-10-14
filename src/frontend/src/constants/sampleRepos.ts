/**
 * 샘플 GitHub 저장소 목록
 */
export const SAMPLE_REPOSITORIES = [
  'https://github.com/facebook/react',
  'https://github.com/microsoft/vscode',
  'https://github.com/nodejs/node',
  'https://github.com/django/django',
  'https://github.com/hong-seongmin/HWnow',
] as const;

/**
 * GitHub URL 유효성 검사 패턴
 */
export const GITHUB_URL_PATTERN = /^https:\/\/github\.com\/[^\/]+\/[^\/]+/;
