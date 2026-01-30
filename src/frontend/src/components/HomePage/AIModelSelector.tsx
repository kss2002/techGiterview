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
      <div className="no-providers" style={{ marginBottom: '1.5rem' }}>
        {isLoading ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            <div
              className="spinner"
              style={{ width: '16px', height: '16px' }}
            ></div>
            <span>AI 모델을 불러오는 중...</span>
          </div>
        ) : (
          '사용 가능한 AI 모델이 없습니다.'
        )}
      </div>
    );
  }

  return (
    <div
      className="grid grid-auto-fit gap-md"
      style={{ marginBottom: '1.5rem' }}
    >
      {providers.map((provider) => {
        const isSelected = selectedAI === provider.id;
        return (
          <label
            key={provider.id}
            className={`card model-card cursor-pointer transition-fast ${isSelected ? 'model-card-selected' : 'model-card-unselected'
              } ${provider.recommended ? 'model-card-recommended' : ''}`}
          >
            <input
              type="radio"
              name="aiProvider"
              value={provider.id}
              checked={isSelected}
              onChange={(e) => onSelectedAIChange(e.target.value)}
              className="form-radio sr-only"
            />
            <div className="card-body" style={{ position: 'relative' }}>
              {/* 선택 상태 체크 아이콘 */}
              {isSelected && (
                <div className="model-check-icon">
                  <CheckCircle size={24} />
                </div>
              )}
              <div className="heading-4 flex items-center justify-between">
                {provider.name}
                {provider.recommended && (
                  <span className="badge badge-success">추천</span>
                )}
              </div>
              <div className="text-body-sm text-muted">{provider.model}</div>
              <div
                className={`text-body-sm ${provider.status === 'ready' ? 'text-success' : 'text-muted'
                  }`}
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
