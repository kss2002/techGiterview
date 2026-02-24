import React from 'react'
import './AppShellV2.css'

interface AppShellV2Props {
  header: React.ReactNode
  sidebar: React.ReactNode
  children: React.ReactNode   // main area
  sidebarWidth: number
  isResizing: boolean
  onResizeStart: (e: React.MouseEvent) => void
  onResizeReset: () => void
  className?: string
}

export function AppShellV2({
  header, sidebar, children,
  sidebarWidth, isResizing, onResizeStart, onResizeReset, className = ''
}: AppShellV2Props) {
  return (
    <div
      className={`v2-root v2-shell ${isResizing ? 'v2-shell--resizing' : ''} ${className}`}
      style={{ '--v2-sidebar-current': `${sidebarWidth}px` } as React.CSSProperties}
    >
      <header className="v2-header">{header}</header>
      <div className="v2-body">
        <aside className="v2-sidebar">
          {sidebar}
          <div
            className={`v2-resize-handle ${isResizing ? 'v2-resize-handle--active' : ''}`}
            onMouseDown={onResizeStart}
            onDoubleClick={onResizeReset}
            role="separator"
            aria-orientation="vertical"
            aria-label="사이드바 너비 조절"
            title="드래그: 너비 조절 / 더블클릭: 초기화"
          />
        </aside>
        <main className="v2-main">{children}</main>
      </div>
    </div>
  )
}
