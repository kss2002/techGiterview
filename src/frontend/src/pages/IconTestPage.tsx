import React from 'react'
import { 
  MessageCircle, 
  Home, 
  BarChart3, 
  FileText, 
  Zap,
  User,
  Bot,
  Send,
  Settings 
} from 'lucide-react'

export const IconTestPage: React.FC = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>SEARCH Lucide React 아이콘 테스트</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <h2>네비게이션 아이콘</h2>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <Home className="w-5 h-5" style={{ color: 'blue' }} />
          <span>홈</span>
          <BarChart3 className="w-5 h-5" style={{ color: 'green' }} />
          <span>대시보드</span>
          <FileText className="w-5 h-5" style={{ color: 'purple' }} />
          <span>리포트</span>
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2>브랜드 아이콘</h2>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <Zap className="w-8 h-8" style={{ color: 'orange' }} />
          <span>TechGiterview</span>
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2>인터뷰 페이지 아이콘</h2>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <MessageCircle className="w-6 h-6" style={{ color: 'teal' }} />
          <span>모의면접</span>
          <User className="w-5 h-5" style={{ color: 'blue' }} />
          <span>사용자</span>
          <Bot className="w-5 h-5" style={{ color: 'red' }} />
          <span>AI</span>
          <Send className="w-5 h-5" style={{ color: 'green' }} />
          <span>전송</span>
          <Settings className="w-5 h-5" style={{ color: 'gray' }} />
          <span>설정</span>
        </div>
      </div>

      <div style={{ 
        padding: '15px', 
        backgroundColor: '#f0f7ff', 
        borderRadius: '8px',
        border: '1px solid #3763e8'
      }}>
        <h3>CHECK 모든 아이콘이 표시되면 설정 완료!</h3>
        <p>
          만약 아이콘이 보이지 않으면 lucide-react 패키지 설치나 import에 문제가 있을 수 있습니다.
        </p>
      </div>
    </div>
  )
}