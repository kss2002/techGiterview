// 디버그 로그를 서버로 전송하는 유틸리티
function sendDebugLog(message, data = null) {
  fetch('/api/debug-log', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      timestamp: new Date().toISOString(),
      message,
      data,
      userAgent: navigator.userAgent,
      url: window.location.href
    })
  }).catch(err => {
    console.error('Failed to send debug log:', err);
  });
}

// 글로벌 에러 핸들러
window.addEventListener('error', (event) => {
  sendDebugLog('JavaScript Error', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error?.stack
  });
});

// 글로벌 Promise rejection 핸들러
window.addEventListener('unhandledrejection', (event) => {
  sendDebugLog('Unhandled Promise Rejection', {
    reason: event.reason?.toString(),
    stack: event.reason?.stack
  });
});

window.sendDebugLog = sendDebugLog;