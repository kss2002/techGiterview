import { useEffect, useRef, useState, type MouseEvent as ReactMouseEvent } from 'react'

interface UseResizableSidebarOptions {
  storageKey: string
  defaultWidth?: number
  minWidth?: number
  maxWidth?: number
}

interface UseResizableSidebarResult {
  width: number
  isResizing: boolean
  startResize: (event: ReactMouseEvent) => void
  resetWidth: () => void
}

export function useResizableSidebar({
  storageKey,
  defaultWidth = 260,
  minWidth = 200,
  maxWidth = 420
}: UseResizableSidebarOptions): UseResizableSidebarResult {
  const [width, setWidth] = useState<number>(() => {
    try {
      const saved = localStorage.getItem(storageKey)
      const parsed = saved ? parseInt(saved, 10) : defaultWidth
      return Number.isFinite(parsed) ? parsed : defaultWidth
    } catch {
      return defaultWidth
    }
  })
  const [isResizing, setIsResizing] = useState(false)
  const widthRef = useRef(width)

  useEffect(() => {
    widthRef.current = width
  }, [width])

  useEffect(() => {
    if (!isResizing) return

    const handleMouseMove = (event: MouseEvent) => {
      const viewportBoundMax = Math.max(minWidth, window.innerWidth - 360)
      const resolvedMax = Math.min(maxWidth, viewportBoundMax)
      const nextWidth = Math.max(minWidth, Math.min(event.clientX, resolvedMax))
      setWidth(nextWidth)
      widthRef.current = nextWidth
    }

    const handleMouseUp = () => {
      setIsResizing(false)
      try {
        localStorage.setItem(storageKey, String(widthRef.current))
      } catch {
        // ignore localStorage errors
      }
    }

    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing, maxWidth, minWidth, storageKey])

  const startResize = (event: ReactMouseEvent) => {
    event.preventDefault()
    setIsResizing(true)
  }

  const resetWidth = () => {
    setWidth(defaultWidth)
    try {
      localStorage.setItem(storageKey, String(defaultWidth))
    } catch {
      // ignore localStorage errors
    }
  }

  return {
    width,
    isResizing,
    startResize,
    resetWidth
  }
}
