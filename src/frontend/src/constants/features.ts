/**
 * 주요 기능 데이터
 */
export const MAIN_FEATURES = [
  {
    id: 'repo-analysis',
    icon: 'CHART',
    title: '저장소 분석',
    description:
      'GitHub 저장소의 코드 구조, 기술 스택, 복잡도를 자동으로 분석합니다.',
  },
  {
    id: 'ai-questions',
    icon: 'AI',
    title: 'AI 질문 생성',
    description:
      '분석 결과를 바탕으로 맞춤형 기술면접 질문을 자동으로 생성합니다.',
  },
  {
    id: 'real-time-interview',
    icon: 'CHAT',
    title: '실시간 모의면접',
    description:
      'WebSocket 기반으로 실제 면접과 같은 환경에서 연습할 수 있습니다.',
  },
  {
    id: 'detailed-report',
    icon: 'CHART',
    title: '상세 리포트',
    description:
      '답변에 대한 AI 평가와 개선 제안을 통해 실력을 향상시킬 수 있습니다.',
  },
] as const;

/**
 * 작동 원리 단계
 */
export const WORKFLOW_STEPS = [
  {
    id: 'input-repo',
    step: 1,
    title: '저장소 입력',
    description: 'GitHub 저장소 URL을 입력하면 자동으로 코드를 분석합니다.',
  },
  {
    id: 'ai-analysis',
    step: 2,
    title: 'AI 분석',
    description: '기술 스택, 코드 품질, 복잡도를 종합적으로 평가합니다.',
  },
  {
    id: 'question-generation',
    step: 3,
    title: '질문 생성',
    description: '분석 결과를 바탕으로 맞춤형 면접 질문을 생성합니다.',
  },
  {
    id: 'mock-interview',
    step: 4,
    title: '모의면접',
    description: '실시간으로 질문에 답하고 즉시 피드백을 받습니다.',
  },
] as const;
