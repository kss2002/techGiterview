/**
 * 높이 매칭 데모 컴포넌트
 * InterviewPage에서 사용할 예시
 */

import React, { useEffect } from 'react';
import { useHeightMatching } from '../utils/heightMatching';

// InterviewPage에서 이렇게 사용하세요:
export const InterviewPageWithHeightMatching: React.FC = () => {
  // 높이 매칭 Hook 사용
  const { manualMatch } = useHeightMatching({
    answerSelector: '.answer-item',
    inputHeaderSelector: '.input-header',
    debounceMs: 150,
    enableVisualFeedback: true
  });

  // 답변이 추가되거나 변경될 때 수동으로 높이 재조정
  const handleAnswerUpdate = () => {
    // 답변 처리 로직...
    
    // 높이 재매칭
    setTimeout(() => {
      manualMatch();
    }, 100);
  };

  return (
    <div className="interview-page">
      {/* 기존 InterviewPage 컴포넌트 내용 */}
      
      {/* 답변 추가/변경 시 manualMatch() 호출 */}
      <button onClick={handleAnswerUpdate}>
        답변 제출
      </button>
    </div>
  );
};

// 또는 더 간단하게 useEffect로 자동 적용:
export const SimpleHeightMatchingExample: React.FC = () => {
  useEffect(() => {
    const { startHeightMatching } = require('../utils/heightMatching');
    
    const matcher = startHeightMatching({
      enableVisualFeedback: true
    });

    return () => {
      matcher.destroy();
    };
  }, []);

  return (
    <div className="interview-content">
      {/* 인터뷰 컨텐츠 */}
    </div>
  );
};