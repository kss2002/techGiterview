import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap } from 'lucide-react';
import { ApiKeySetup } from '../components/ApiKeySetup';
import { QuickAccessSection } from '../components/QuickAccessSection';
import { usePageInitialization } from '../hooks/usePageInitialization';
import {
  ApiKeySetupCard,
  AISelectionAndAnalysisCard,
  SampleRepositoriesSection,
  MainFeaturesSection,
  WorkflowSection,
  HomePageFooter,
} from '../components/HomePage';
import { handleRepositoryAnalysis } from '../utils/repositoryAnalysisService';
import type { HomePageState } from '../types/homePage';
import Particles from '@/ui/Particles';
import AnimatedContent from '@/ui/AnimatedContent';
import './HomePage.css';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();

  let maintitle = 'TechGiterview';
  let subtitle = 'GitHub 저장소를 분석하여 맞춤형 기술면접을 준비하세요';
  let desc =
    'AI가 당신의 코드를 분석하고 실제 면접에서 나올 수 있는 질문들을 생성합니다. 실시간 모의면접으로 완벽한 준비를 해보세요.';

  // 모든 초기화 로직을 Hook으로 위임
  const {
    config,
    providers,
    selectedAI,
    setSelectedAI,
    isLoading,
    error,
    isUsingLocalData,
    hasStoredKeys,
    refreshStoredKeysState,
    createApiHeaders,
  } = usePageInitialization();

  // 컴포넌트 상태 (최소화)
  const [state, setState] = useState<HomePageState>({
    repoUrl: '',
    isAnalyzing: false,
    showApiKeySetup: false,
  });

  // API 키 설정 모달 표시 여부 결정 - 사용자가 버튼 클릭 시에만 표시
  const shouldShowApiKeySetup = state.showApiKeySetup;

  // 키가 없을 때 버튼 강조 여부
  const needsApiKeySetup = config.keys_required && !hasStoredKeys();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!state.repoUrl.trim() || !selectedAI) return;

    setState((prev) => ({ ...prev, isAnalyzing: true }));

    try {
      const result = await handleRepositoryAnalysis(
        state.repoUrl,
        createApiHeaders,
        navigate
      );

      if (!result.success) {
        if (result.shouldShowApiKeySetup) {
          setState((prev) => ({ ...prev, showApiKeySetup: true }));
          alert(result.error + '\n\nAPI 키 설정 창을 열어드립니다.');
        } else {
          alert(result.error);
        }
      }
    } catch (error) {
      console.error('Analysis error:', error);
      alert('예상치 못한 오류가 발생했습니다.');
    } finally {
      setState((prev) => ({ ...prev, isAnalyzing: false }));
    }
  };

  // 헬퍼 함수들
  const updateState = (updates: Partial<HomePageState>) => {
    setState((prev) => ({ ...prev, ...updates }));
  };

  const handleApiKeysSet = () => {
    refreshStoredKeysState();
    updateState({ showApiKeySetup: false });
  };

  return (
    <div className="home-page">
      <Particles
        particleColors={['#18167797', '#18167775']}
        particleCount={500}
        particleSpread={10}
        speed={0.2}
        particleBaseSize={150}
        moveParticlesOnHover={false}
        alphaParticles={true}
        disableRotation={true}
      />
      <AnimatedContent
        distance={150}
        direction="vertical"
        reverse={false}
        duration={1.2}
        ease="bounce.out"
        initialOpacity={0.2}
        animateOpacity
        scale={1.1}
        threshold={0.2}
        delay={0.3}
      >
        <section className="section">
          <div className="container">
            <h1 className="heading-1 text-center">
              <Zap className="title-icon" aria-hidden="true" />
              {maintitle}
            </h1>
            <p className="text-subtitle text-center">{subtitle}</p>
            <p className="text-lead text-center">{desc}</p>
          </div>

          <div className="container">
            {/* API 키 설정 버튼 */}
            <ApiKeySetupCard
              onShowApiKeySetup={() => updateState({ showApiKeySetup: true })}
              isUsingLocalData={isUsingLocalData}
              error={error}
              isLoading={isLoading}
              needsSetup={needsApiKeySetup}
            />

            {/* AI 모델 선택 및 분석 시작 통합 섹션 */}
            <AISelectionAndAnalysisCard
              providers={providers}
              selectedAI={selectedAI}
              onSelectedAIChange={setSelectedAI}
              isLoading={isLoading}
              repoUrl={state.repoUrl}
              isAnalyzing={state.isAnalyzing}
              onRepoUrlChange={(url) => updateState({ repoUrl: url })}
              onSubmit={handleSubmit}
            />

            <SampleRepositoriesSection
              onRepoSelect={(url) => updateState({ repoUrl: url })}
              isAnalyzing={state.isAnalyzing}
            />
          </div>
        </section>

        {/* 최근 활동 섹션 */}
        <section className="section bg-gray-50">
          <div className="container">
            <QuickAccessSection />
          </div>
        </section>

        {/* 기능 섹션 */}
        <MainFeaturesSection />

        {/* 작동 원리 */}
        <WorkflowSection />
      </AnimatedContent>

      {/* API 키 설정 모달 */}
      {shouldShowApiKeySetup && (
        <ApiKeySetup
          onApiKeysSet={handleApiKeysSet}
          onClose={() => updateState({ showApiKeySetup: false })}
        />
      )}

      {/* 푸터 */}
      <HomePageFooter />
    </div>
  );
};
