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
          <path d="M20.216 6.415l-.132-.666c-.119-.598-.388-1.163-.766-1.68a4.448 4.448 0.015-.571-1.364c-.263-.414-.618-.796-.53-.236-1.295.1-.295.317-.54.632-.688.645-.296.967-.767 1.161-1.394l.132-.666a2.25 2.25 0 01.872-1.39 2.207 2.207 0 011.482-.211l.132.666c.119.598.388 1.163.766 1.68.378.516.82.95 1.364 1.24.236.163.54.317.688.632.296.645.296.967.767 1.161z"/>
          <path d="M6.716 7.197l3.934 4.825-2.375 4.626c-.117.228-.311.362-.518.362-.417 0-.656-.357-.518-.724l1.597-3.11L5.45 8.901c-.258-.317-.297-.748-.094-1.1.204-.353.602-.547.987-.547.4 0 .737.211.937.526l.436.417z"/>
          <path d="M12.5 18.323c-.727 0-1.323-.596-1.323-1.323s.596-1.323 1.323-1.323 1.323.596 1.323 1.323-.596 1.323-1.323 1.323zm0-1.646c-.178 0-.323.145-.323.323s.145.323.323.323.323-.145.323-.323-.145-.323-.323-.323z"/>
          <path d="M18.5 8c1.381 0 2.5 1.119 2.5 2.5v4c0 1.381-1.119 2.5-2.5 2.5h-1v-1h1c.827 0 1.5-.673 1.5-1.5v-4c0-.827-.673-1.5-1.5-1.5h-1v-1h1zm-13 0h1v1h-1c-.827 0-1.5.673-1.5 1.5v4c0 .827.673 1.5 1.5 1.5h1v1h-1c-1.381 0-2.5-1.119-2.5-2.5v-4c0-1.381 1.119-2.5 2.5-2.5z"/>
          <path d="M7.5 9h9c.276 0 .5.224.5.5v6c0 .276-.224.5-.5.5h-9c-.276 0-.5-.224-.5-.5v-6c0-.276.224-.5.5-.5zm.5 1v5h8v-5h-8z"/>
        </svg>
      </button>
    </div>
  )
}