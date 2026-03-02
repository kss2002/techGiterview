import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiKeySetup } from '../components/ApiKeySetup';
import { QuickAccessSection } from '../components/QuickAccessSection';
import { usePageInitialization } from '../hooks/usePageInitialization';
import {
  ApiKeySetupCard,
  HomePageFooter,
  HomePageNavbar,
  RepositoryAnalysisForm,
  SampleRepositoriesSection,
} from '../components/HomePage';
import { handleRepositoryAnalysis } from '../utils/repositoryAnalysisService';
import type { HomePageState } from '../types/homePage';
import './HomePage.css';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const {
    config,
    providers,
    selectedAI,
    setSelectedAI,
    isLoading,
    error,
    isUsingLocalData,
    hasStoredKeys,
    createApiHeaders,
  } = usePageInitialization();

  const [state, setState] = useState<HomePageState>({
    repoUrl: '',
    isAnalyzing: false,
    showApiKeySetup: false,
  });

  const shouldShowApiKeySetup = state.showApiKeySetup;
  const needsApiKeySetup = config.keys_required && !hasStoredKeys();

  const updateState = (updates: Partial<HomePageState>) => {
    setState((prev) => ({ ...prev, ...updates }));
  };

  const createApiHeadersForAnalysis = (includeApiKeys: boolean, _selectedAI?: string) =>
    createApiHeaders(includeApiKeys);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!state.repoUrl.trim() || !selectedAI) return;

    updateState({ isAnalyzing: true });

    try {
      const result = await handleRepositoryAnalysis(
        state.repoUrl,
        createApiHeadersForAnalysis,
        selectedAI,
        navigate
      );

      if (!result.success) {
        if (result.shouldShowApiKeySetup) {
          updateState({ showApiKeySetup: true });
        }
        if (result.error) {
          alert(result.error);
        }
      }
    } catch (submitError) {
      console.error('Analysis error:', submitError);
      alert('예상치 못한 오류가 발생했습니다.');
    } finally {
      updateState({ isAnalyzing: false });
    }
  };

  const handleApiKeysSet = () => {
    updateState({ showApiKeySetup: false });
  };

  return (
    <div className="home-page">
      <HomePageNavbar
        onShowApiKeySetup={() => updateState({ showApiKeySetup: true })}
        needsApiKeySetup={needsApiKeySetup}
        isConnected={!error && !isLoading}
        providers={providers}
        selectedAI={selectedAI}
        onSelectedAIChange={setSelectedAI}
      />

      <section className="search-hero-section">
        <div className="home-search-shell">
          <h1 className="home-search-title">분석할 GitHub 저장소를 입력하세요</h1>

          <ApiKeySetupCard
            onShowApiKeySetup={() => updateState({ showApiKeySetup: true })}
            isUsingLocalData={isUsingLocalData}
            error={error as Error | string | null}
            isLoading={isLoading}
            needsSetup={needsApiKeySetup}
          />

          <div className="main-search-container">
            <RepositoryAnalysisForm
              repoUrl={state.repoUrl}
              isAnalyzing={state.isAnalyzing}
              selectedAI={selectedAI}
              onRepoUrlChange={(url) => updateState({ repoUrl: url })}
              onSubmit={handleSubmit}
            />
          </div>

          <SampleRepositoriesSection
            onRepoSelect={(url) => updateState({ repoUrl: url })}
            isAnalyzing={state.isAnalyzing}
          />
        </div>
      </section>

      <section className="section bg-gray-50">
        <div className="container">
          <QuickAccessSection />
        </div>
      </section>

      {shouldShowApiKeySetup && <ApiKeySetup onApiKeysSet={handleApiKeysSet} />}

      <HomePageFooter />
    </div>
  );
};
