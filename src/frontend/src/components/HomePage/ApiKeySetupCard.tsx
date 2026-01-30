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
  // isUsingLocalData is kept in interface for API compatibility but not used in this simplified version
  error,
  isLoading,
  needsSetup = false,
}) => {

  // 서버 연결 상태 확인
  const isConnected = !error && !isLoading;

  return (
    <div className={`card card-compact ${needsSetup ? 'card-warning' : ''}`}>
      <div className="card-body flex justify-between items-center">
        <div className="flex items-center gap-sm">
          <h3 className="heading-4 flex items-center gap-sm" style={{ marginBottom: 0 }}>
            <Key className="icon" />
            API 키 설정
          </h3>
          {/* 상태 배지: 타이틀 옆으로 이동 */}
          {needsSetup ? (
            <span className="badge badge-warning" style={{ fontSize: '11px' }}>
              <AlertCircle style={{ width: '12px', height: '12px', marginRight: '4px' }} />
              설정 필요
            </span>
          ) : isConnected ? (
            <span className="badge badge-success" style={{ fontSize: '11px' }}>
              <CheckCircle2 style={{ width: '12px', height: '12px', marginRight: '4px' }} />
              연결됨
            </span>
          ) : null}
        </div>
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
          {needsSetup ? '🔑 키 입력하기' : '설정 변경'}
        </button>
      </div>

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
