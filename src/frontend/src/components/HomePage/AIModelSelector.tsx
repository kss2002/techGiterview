import React from 'react';

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
      {providers.map((provider) => (
        <label
          key={provider.id}
          className={`card hover-lift-sm cursor-pointer transition-fast ${
            selectedAI === provider.id ? 'border-primary-500 bg-primary-50' : ''
          } ${provider.recommended ? 'border-brand-green-300' : ''}`}
        >
          <input
            type="radio"
            name="aiProvider"
            value={provider.id}
            checked={selectedAI === provider.id}
            onChange={(e) => onSelectedAIChange(e.target.value)}
            className="form-radio sr-only"
          />
          <div className="card-body">
            <div className="heading-4 flex items-center justify-between">
              {provider.name}
              {provider.recommended && (
                <span className="badge badge-success">추천</span>
              )}
            </div>
            <div className="text-body-sm text-muted">{provider.model}</div>
            <div
              className={`text-body-sm ${
                provider.status === 'ready' ? 'text-success' : 'text-muted'
              }`}
            >
              {provider.status === 'ready' ? '● 사용 가능' : '○ 설정됨'}
            </div>
          </div>
        </label>
      ))}
    </div>
  );
};
