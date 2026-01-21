import React from 'react';
import { Key, Settings, AlertCircle } from 'lucide-react';
import { StatusIndicators } from './StatusIndicators';

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
  return (
    <div className={`card ${needsSetup ? 'card-warning' : ''}`}>
      <div className="card-body flex justify-between items-center">
        <h3 className="heading-4 flex items-center gap-sm">
          <Key className="icon" />
          API 키 설정
          {needsSetup && (
            <span className="badge badge-warning" style={{ marginLeft: '8px', fontSize: '12px' }}>
              <AlertCircle className="icon" style={{ width: '14px', height: '14px', marginRight: '4px' }} />
              설정 필요
            </span>
          )}
        </h3>
        <button
          className={`btn ${needsSetup ? 'btn-warning pulse-animation' : 'btn-outline'} btn-sm hover-scale-sm active-scale-sm focus-ring`}
          onClick={onShowApiKeySetup}
          type="button"
          style={needsSetup ? {
            backgroundColor: '#f59e0b',
            color: 'white',
            borderColor: '#f59e0b',
            animation: 'pulse 2s infinite'
          } : {}}
        >
          <Settings className="icon" />
          {needsSetup ? '🔑 API 키 입력하기' : 'API 키 설정'}
        </button>
      </div>

      <StatusIndicators
        isUsingLocalData={isUsingLocalData}
        error={error}
        isLoading={isLoading}
      />

      {needsSetup && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#fef3c7',
          borderTop: '1px solid #fcd34d',
          fontSize: '14px',
          color: '#92400e'
        }}>
          ⚠️ 서비스를 이용하려면 GitHub 토큰과 AI API 키가 필요합니다.
        </div>
      )}
    </div>
  );
};
