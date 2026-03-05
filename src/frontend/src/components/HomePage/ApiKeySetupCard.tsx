import React from 'react';
import { Key, Settings, AlertCircle, CheckCircle2 } from 'lucide-react';

interface ApiKeySetupCardProps {
  onShowApiKeySetup: () => void;
  isUsingLocalData: boolean;
  error: Error | string | null;
  isLoading: boolean;
  needsSetup?: boolean;
}

export const ApiKeySetupCard: React.FC<ApiKeySetupCardProps> = ({
  onShowApiKeySetup,
  isUsingLocalData,
  error,
  isLoading,
  needsSetup = false,
}) => {
  const isConnected = !error && !isLoading;
  const statusLabel = needsSetup ? '설정 필요' : isConnected ? '연결됨' : isUsingLocalData ? '로컬 모드' : '확인 필요';
  const statusClass = needsSetup
    ? 'home-api-status--warning'
    : isConnected
      ? 'home-api-status--success'
      : 'home-api-status--neutral';
  const stepClass = needsSetup
    ? 'home-api-step-badge--warning'
    : isConnected
      ? 'home-api-step-badge--success'
      : 'home-api-step-badge--neutral';
  const cardStateClass = needsSetup
    ? 'home-api-key-card--warning'
    : isConnected
      ? 'home-api-key-card--success'
      : 'home-api-key-card--neutral';

  return (
    <div className={`home-api-key-card ${cardStateClass}`}>
      <div className="home-api-key-card-body">
        <div className="home-api-key-main">
          <span className={`home-api-step-badge ${stepClass}`} aria-hidden="true">
            1
          </span>
          <div className="home-api-key-text">
            <h3 className="home-api-key-title">
              <Key className="v2-icon-sm home-api-key-title-icon" />
              Step 1. API 키 설정
            </h3>
            <p className="home-api-key-copy">
              Upstage 또는 Google API 키 중 하나만 설정하면 바로 분석을 시작할 수 있습니다.
            </p>
          </div>
          <span className={`home-api-status-chip ${statusClass}`}>
            {needsSetup ? (
              <AlertCircle className="v2-icon-xs" />
            ) : (
              <CheckCircle2 className="v2-icon-xs" />
            )}
            {statusLabel}
          </span>
        </div>
        <button
          className={`home-api-key-btn ${needsSetup ? 'home-api-key-btn--warning' : ''}`}
          onClick={onShowApiKeySetup}
          type="button"
        >
          <Settings className="v2-icon-sm" />
          {needsSetup ? '키 입력하기' : '설정 변경'}
        </button>
      </div>

      {needsSetup && (
        <div className="home-api-key-notice">
          ⚠️ GitHub 토큰은 선택 사항이며, AI API 키(Upstage/Google) 중 하나는 필수입니다.
        </div>
      )}
    </div>
  );
};
