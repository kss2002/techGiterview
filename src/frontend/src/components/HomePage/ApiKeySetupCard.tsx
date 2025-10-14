import React from 'react';
import { Key, Settings } from 'lucide-react';
import { StatusIndicators } from './StatusIndicators';

interface ApiKeySetupCardProps {
  onShowApiKeySetup: () => void;
  isUsingLocalData: boolean;
  error: Error | string | null;
  isLoading: boolean;
}

export const ApiKeySetupCard: React.FC<ApiKeySetupCardProps> = ({
  onShowApiKeySetup,
  isUsingLocalData,
  error,
  isLoading,
}) => {
  return (
    <div className="card">
      <div className="card-body flex justify-between items-center">
        <h3 className="heading-4 flex items-center gap-sm">
          <Key className="icon" />
          API 키 설정
        </h3>
        <button
          className="btn btn-outline btn-sm hover-scale-sm active-scale-sm focus-ring"
          onClick={onShowApiKeySetup}
          type="button"
        >
          <Settings className="icon" />
          API 키 설정
        </button>
      </div>

      <StatusIndicators
        isUsingLocalData={isUsingLocalData}
        error={error}
        isLoading={isLoading}
      />
    </div>
  );
};
