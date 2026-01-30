import React from 'react';
import { SAMPLE_REPOSITORIES } from '../../constants/sampleRepos';
import { extractRepoName } from '../../utils/homePageUtils';

interface SampleRepositoriesSectionProps {
  onRepoSelect: (url: string) => void;
  isAnalyzing: boolean;
}

export const SampleRepositoriesSection: React.FC<
  SampleRepositoriesSectionProps
> = ({ onRepoSelect, isAnalyzing }) => {
  return (
    <div className="sample-repos-section">
      <p className="sample-repos-label">예시로 시작하기</p>
      <div className="sample-repo-chips">
        {SAMPLE_REPOSITORIES.map((repo, index) => (
          <button
            key={index}
            onClick={() => onRepoSelect(repo)}
            className="sample-repo-chip"
            disabled={isAnalyzing}
          >
            {extractRepoName(repo)}
          </button>
        ))}
      </div>
    </div>
  );
};
