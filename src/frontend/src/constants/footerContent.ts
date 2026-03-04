export interface FooterLinkItem {
  key: 'email' | 'repository' | 'issues' | 'docs';
  label: string;
  href: string;
}

export interface FooterSimpleLinkItem {
  label: string;
  href: string;
}

export const FOOTER_BRAND_DESCRIPTION = 'GitHub 기반 AI 기술면접 준비 플랫폼';

export const FOOTER_FEATURE_ITEMS = [
  '저장소 자동 분석',
  '맞춤형 질문 생성',
  '실시간 모의면접',
  '상세 피드백 리포트',
] as const;

export const FOOTER_SUPPORTED_TECH_ITEMS = [
  'Python, JavaScript, TypeScript',
  'React, Vue, Angular',
  'Node.js, Django, FastAPI',
  '그 외 다양한 언어와 프레임워크',
] as const;

export const FOOTER_CONTACT_ITEMS: FooterLinkItem[] = [
  {
    key: 'email',
    label: 'hong112424@naver.com',
    href: 'mailto:hong112424@naver.com',
  },
  {
    key: 'repository',
    label: 'GitHub Repository',
    href: 'https://github.com/hong-seongmin/techGiterview',
  },
  {
    key: 'issues',
    label: 'GitHub Issues',
    href: 'https://github.com/hong-seongmin/techGiterview/issues',
  },
  {
    key: 'docs',
    label: 'Documentation (README)',
    href: 'https://github.com/hong-seongmin/techGiterview#readme',
  },
];

export const FOOTER_LEGAL_ITEMS: FooterSimpleLinkItem[] = [
  {
    label: 'README',
    href: 'https://github.com/hong-seongmin/techGiterview#readme',
  },
  {
    label: 'LICENSE',
    href: 'https://github.com/hong-seongmin/techGiterview/blob/main/LICENSE',
  },
];
