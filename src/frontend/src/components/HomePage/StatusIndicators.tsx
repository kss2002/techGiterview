import React from 'react';
import { HardDrive, AlertTriangle, CheckCircle } from 'lucide-react';

interface StatusIndicatorsProps {
  isUsingLocalData: boolean;
  error: Error | string | null;
  isLoading: boolean;
}

export const StatusIndicators: React.FC<StatusIndicatorsProps> = ({
  isUsingLocalData,
  error,
  isLoading,
}) => {
  return (
    <div className="status-indicators">
      {isUsingLocalData && (
        <div className="status-badge local">
          <HardDrive className="icon" />
          로컬 데이터 사용 중
        </div>
      )}
      {error && (
        <div className="status-badge error">
          <AlertTriangle className="icon" />
          서버 연결 오류 (오프라인 모드)
        </div>
      )}
      {!isLoading && !error && !isUsingLocalData && (
        <div className="status-badge online">
          <CheckCircle className="icon" />
          서버 연결됨
        </div>
      )}
    </div>
  );
};
