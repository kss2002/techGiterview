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
    <div className="card">
      <div className="card-body text-center">
        <p className="text-body">샘플 저장소로 체험해보기:</p>
        <div className="flex flex-wrap justify-center gap-sm">
          {SAMPLE_REPOSITORIES.map((repo, index) => (
            <button
              key={index}
              onClick={() => onRepoSelect(repo)}
              className="btn btn-ghost btn-sm hover-scale-sm active-scale-sm focus-ring"
              disabled={isAnalyzing}
            >
              {extractRepoName(repo)}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
