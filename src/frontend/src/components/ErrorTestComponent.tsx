import React, { useState } from 'react'

export const ErrorTestComponent: React.FC = () => {
  const [shouldThrow, setShouldThrow] = useState(false)

  if (shouldThrow) {
    throw new Error('이것은 의도적으로 발생시킨 테스트 에러입니다!')
  }

  return (
    <div className="debug-container">
      <h1 className="debug-title">Error Boundary 테스트</h1>
      <p className="debug-text">아래 버튼을 클릭하면 ErrorBoundary가 에러를 잡아서 표시합니다.</p>
      <button 
        className="btn btn-error"
        onClick={() => setShouldThrow(true)}
      >
        에러 발생시키기
      </button>
    </div>
  )
}