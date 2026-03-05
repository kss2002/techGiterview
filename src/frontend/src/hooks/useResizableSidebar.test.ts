import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { useResizableSidebar } from './useResizableSidebar'

describe('useResizableSidebar', () => {
  it('uses persisted width when available', () => {
    localStorage.setItem('sidebar_test_width', '312')

    const { result } = renderHook(() =>
      useResizableSidebar({
        storageKey: 'sidebar_test_width',
        defaultWidth: 260
      })
    )

    expect(result.current.width).toBe(312)
  })

  it('resets width to default and persists it', () => {
    localStorage.setItem('sidebar_test_reset', '351')

    const { result } = renderHook(() =>
      useResizableSidebar({
        storageKey: 'sidebar_test_reset',
        defaultWidth: 280
      })
    )

    act(() => {
      result.current.resetWidth()
    })

    expect(result.current.width).toBe(280)
    expect(localStorage.getItem('sidebar_test_reset')).toBe('280')
  })
})
