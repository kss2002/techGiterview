import React from 'react';
import { AIModelSelector } from './AIModelSelector';
import { RepositoryAnalysisForm } from './RepositoryAnalysisForm';

interface AIProvider {
  id: string;
  name: string;
  model: string;
  status: string;
  recommended?: boolean;
}

interface AISelectionAndAnalysisCardProps {
  providers: AIProvider[];
  selectedAI: string;
  onSelectedAIChange: (aiId: string) => void;
  isLoading: boolean;
  repoUrl: string;
  isAnalyzing: boolean;
  onRepoUrlChange: (url: string) => void;
  onSubmit: (e: React.FormEvent) => void;
}

export const AISelectionAndAnalysisCard: React.FC<
  AISelectionAndAnalysisCardProps
> = ({
  providers,
  selectedAI,
  onSelectedAIChange,
  isLoading,
  repoUrl,
  isAnalyzing,
  onRepoUrlChange,
  onSubmit,
}) => {
  return (
    <div className="card">
      <div className="card-body">
        <h3 className="heading-4 flex items-center gap-sm">
          AI 모델 선택 및 분석 시작
        </h3>

        {/* AI 모델 선택 */}
        <AIModelSelector
          providers={providers}
          selectedAI={selectedAI}
          onSelectedAIChange={onSelectedAIChange}
          isLoading={isLoading}
        />

        {/* 분석 시작 폼 */}
        <RepositoryAnalysisForm
          repoUrl={repoUrl}
          isAnalyzing={isAnalyzing}
          selectedAI={selectedAI}
          onRepoUrlChange={onRepoUrlChange}
          onSubmit={onSubmit}
        />
      </div>
    </div>
  );
};
