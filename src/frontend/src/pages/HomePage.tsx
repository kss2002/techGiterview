import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiKeySetup } from '../components/ApiKeySetup';
import { QuickAccessSection } from '../components/QuickAccessSection';
import { usePageInitialization } from '../hooks/usePageInitialization';
import {
  SampleRepositoriesSection,
  HomePageFooter,
  HomePageNavbar,
  RepositoryAnalysisForm,
} from '../components/HomePage';
import { handleRepositoryAnalysis } from '../utils/repositoryAnalysisService'
import type { HomePageState } from '../types/homePage';
import './HomePage.css';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();

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
      {/* Top Navigation Bar */}
      <HomePageNavbar
        onShowApiKeySetup={() => updateState({ showApiKeySetup: true })}
        needsApiKeySetup={needsApiKeySetup}
        isConnected={!error && !isLoading}
        providers={providers}
        selectedAI={selectedAI}
        onSelectedAIChange={setSelectedAI}
      />

      {/* Centered Search Hero - ULTRA-MINIMAL */}
      <section className="search-hero-section">
        <div style={{ maxWidth: '640px', margin: '0 auto', textAlign: 'center', padding: '0 1.5rem' }}>

          {/* Simple Title */}
          <h1 style={{
            fontSize: '1.75rem',
            fontWeight: 500,
            color: '#171717',
            marginBottom: '2rem',
            letterSpacing: '-0.01em'
          }}>
            분석할 GitHub 저장소를 입력하세요
          </h1>

          {/* The Main Search Input */}
          <div className="main-search-container">
            <RepositoryAnalysisForm
              repoUrl={state.repoUrl}
              isAnalyzing={state.isAnalyzing}
              selectedAI={selectedAI}
              onRepoUrlChange={(url: string) => updateState({ repoUrl: url })}
              onSubmit={handleSubmit}
            />
          </div>

          {/* Sample links */}
          <div style={{ marginTop: '2.5rem' }}>
            <SampleRepositoriesSection
              onRepoSelect={(url: string) => updateState({ repoUrl: url })}
              isAnalyzing={state.isAnalyzing}
            />
          </div>

        </div>
      </section>

      {/* Recent Activity - Simple section */}
      <section style={{ padding: '3rem 1.5rem', background: '#fafafa', borderTop: '1px solid #e5e5e5' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <QuickAccessSection />
        </div>
      </section>

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
