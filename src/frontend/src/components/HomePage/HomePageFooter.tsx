import React from 'react';
import { Zap } from 'lucide-react';

export const HomePageFooter: React.FC = () => {
  return (
    <footer className="homepage-footer">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section">
            <h3>
              <Zap className="icon" />
              TechGiterview
            </h3>
            <p>GitHub 기반 AI 기술면접 준비 플랫폼</p>
          </div>

          <div className="footer-section">
            <h4>링크</h4>
            <div className="footer-links">
              <a
                href="https://github.com/hong-seongmin/techGiterview"
                target="_blank"
                rel="noopener noreferrer"
                className="footer-link"
              >
                GitHub Repository
              </a>
              <a
                href="https://buymeacoffee.com/oursophy"
                target="_blank"
                rel="noopener noreferrer"
                className="footer-link"
              >
                Buy Me a Coffee
              </a>
            </div>
          </div>

          <div className="footer-section">
            <h4>연락처</h4>
            <ul>
              <li>EMAIL hong112424@naver.com</li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2025 TechGiterview. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};
