import React from 'react';
import { CheckCircle } from 'lucide-react';

interface AIProvider {
  id: string;
  name: string;
  model: string;
  status: string;
  recommended?: boolean;
}

interface AIModelSelectorProps {
  providers: AIProvider[];
  selectedAI: string;
  onSelectedAIChange: (aiId: string) => void;
  isLoading: boolean;
}

export const AIModelSelector: React.FC<AIModelSelectorProps> = ({
  providers,
  selectedAI,
  onSelectedAIChange,
  isLoading,
}) => {
  if (providers.length === 0) {
    return (
      <div className="home-model-selector-empty">
        {isLoading ? (
          <div className="home-model-selector-loading">
            <div className="spinner home-model-selector-spinner"></div>
            <span>AI 모델을 불러오는 중...</span>
          </div>
        ) : (
          '사용 가능한 AI 모델이 없습니다.'
        )}
      </div>
    );
  }

  return (
    <div className="home-model-selector-grid">
      {providers.map((provider) => {
        const isSelected = selectedAI === provider.id;

        return (
          <label
            key={provider.id}
            className={`home-model-card ${isSelected ? 'home-model-card--selected' : ''} ${provider.recommended ? 'home-model-card--recommended' : ''}`}
          >
            <input
              type="radio"
              name="aiProvider"
              value={provider.id}
              checked={isSelected}
              onChange={(e) => onSelectedAIChange(e.target.value)}
              className="v2-sr-only"
            />
            <div className="home-model-card-body">
              {isSelected && (
                <div className="home-model-check-icon">
                  <CheckCircle className="v2-icon-lg" />
                </div>
              )}

              <div className="home-model-card-title-row">
                <h4 className="home-model-card-title">{provider.name}</h4>
                {provider.recommended && (
                  <span className="home-model-card-chip">추천</span>
                )}
              </div>

              <div className="home-model-card-model">{provider.model}</div>
              <div
                className={`home-model-card-status ${provider.status === 'ready' ? 'home-model-card-status--ready' : ''}`}
              >
                {provider.status === 'ready' ? '● 사용 가능' : '○ 설정됨'}
              </div>
            </div>
          </label>
        );
      })}
    </div>
  );
};
