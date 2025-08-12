import React from 'react'
import './FloatingLinks.css'

export const FloatingLinks: React.FC = () => {
  const handleBMCClick = (e: React.MouseEvent) => {
    e.preventDefault()
    
    // BMC 위젯의 실제 버튼을 찾아서 클릭
    setTimeout(() => {
      const bmcButton = document.querySelector('img[alt*="Buy Me A Coffee"]') as HTMLElement
      if (bmcButton) {
        bmcButton.click()
        return
      }
      
      // 다른 방법으로 BMC 위젯 버튼 찾기
      const bmcElements = document.querySelectorAll('[data-name*="BMC"], [id*="bmc"], img[src*="buymeacoffee"]')
      for (let element of bmcElements) {
        const htmlElement = element as HTMLElement
        if (htmlElement && htmlElement.click) {
          htmlElement.click()
          return
        }
      }
      
      // 위젯을 찾지 못한 경우만 외부 링크로 이동
      window.open('https://buymeacoffee.com/oursophy', '_blank')
    }, 500)
  }

  return (
    <div className="floating-links">
      <a
        href="https://github.com/hong-seongmin/techGiterview"
        target="_blank"
        rel="noopener noreferrer"
        className="floating-link github"
        data-tooltip="GitHub Repository"
        aria-label="GitHub Repository"
      >
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
        </svg>
      </a>
      
      <button
        onClick={handleBMCClick}
        className="floating-link coffee"
        data-tooltip="Buy Me a Coffee"
        aria-label="Support on Buy Me a Coffee"
      >
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M7.5 3h9c1.4 0 2.5 1.1 2.5 2.5v1c0 .6-.4 1-1 1s-1-.4-1-1v-1c0-.3-.2-.5-.5-.5h-9c-.3 0-.5.2-.5.5v13c0 .3.2.5.5.5h9c.3 0 .5-.2.5-.5v-1c0-.6.4-1 1-1s1 .4 1 1v1c0 1.4-1.1 2.5-2.5 2.5h-9C6.1 21 5 19.9 5 18.5v-13C5 4.1 6.1 3 7.5 3z"/>
          <path d="M12 8c2.2 0 4 1.8 4 4s-1.8 4-4 4-4-1.8-4-4 1.8-4 4-4zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
          <path d="M18 11h2v2h-2z"/>
        </svg>
      </button>
    </div>
  )
}