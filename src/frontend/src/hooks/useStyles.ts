/**
 * TechGiterview 동적 스타일링 Hook 시스템
 * 
 * 인라인 스타일을 대체하기 위한 React Hook 기반 스타일 관리 시스템입니다.
 * CSS 클래스와 동적 스타일을 조합하여 유연한 스타일링을 제공합니다.
 */

import { useMemo } from 'react'

// 색상 타입 정의
type ColorVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'gray'
type ColorShade = 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900

// 간격 타입 정의
type SpacingSize = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 16 | 20 | 24

// 그림자 타입 정의
type ShadowSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl'

// 테두리 둥글기 타입 정의
type RadiusSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'

// 스타일 옵션 인터페이스
interface StyleOptions {
  color?: ColorVariant
  shade?: ColorShade
  background?: ColorVariant
  backgroundShade?: ColorShade
  padding?: SpacingSize
  margin?: SpacingSize
  shadow?: ShadowSize
  radius?: RadiusSize
  border?: boolean
  borderColor?: ColorVariant
  fontSize?: 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | '3xl'
  fontWeight?: 'normal' | 'medium' | 'semibold' | 'bold'
  textAlign?: 'left' | 'center' | 'right'
  width?: string | number
  height?: string | number
  maxWidth?: string | number
}

/**
 * 동적 스타일 생성을 위한 Hook
 */
export function useStyles(options: StyleOptions = {}) {
  const styles = useMemo(() => {
    const classNames: string[] = []
    const inlineStyles: React.CSSProperties = {}

    // 배경 색상
    if (options.background) {
      if (options.backgroundShade) {
        classNames.push(`bg-${options.background}-${options.backgroundShade}`)
      } else {
        classNames.push(`bg-${options.background}`)
      }
    }

    // 텍스트 색상
    if (options.color) {
      if (options.shade) {
        classNames.push(`text-${options.color}-${options.shade}`)
      } else {
        classNames.push(`text-${options.color}`)
      }
    }

    // 패딩
    if (options.padding !== undefined) {
      inlineStyles.padding = `var(--spacing-${options.padding})`
    }

    // 마진
    if (options.margin !== undefined) {
      inlineStyles.margin = `var(--spacing-${options.margin})`
    }

    // 그림자
    if (options.shadow) {
      inlineStyles.boxShadow = `var(--shadow-${options.shadow})`
    }

    // 테두리 둥글기
    if (options.radius) {
      inlineStyles.borderRadius = `var(--radius-${options.radius})`
    }

    // 테두리
    if (options.border) {
      inlineStyles.border = '1px solid'
      if (options.borderColor) {
        inlineStyles.borderColor = `var(--${options.borderColor}-300)`
      } else {
        inlineStyles.borderColor = 'var(--gray-300)'
      }
    }

    // 폰트 크기
    if (options.fontSize) {
      inlineStyles.fontSize = `var(--text-${options.fontSize})`
    }

    // 폰트 굵기
    if (options.fontWeight) {
      inlineStyles.fontWeight = `var(--font-${options.fontWeight})`
    }

    // 텍스트 정렬
    if (options.textAlign) {
      inlineStyles.textAlign = options.textAlign
    }

    // 너비
    if (options.width !== undefined) {
      inlineStyles.width = typeof options.width === 'number' ? `${options.width}px` : options.width
    }

    // 높이
    if (options.height !== undefined) {
      inlineStyles.height = typeof options.height === 'number' ? `${options.height}px` : options.height
    }

    // 최대 너비
    if (options.maxWidth !== undefined) {
      inlineStyles.maxWidth = typeof options.maxWidth === 'number' ? `${options.maxWidth}px` : options.maxWidth
    }

    return {
      className: classNames.join(' '),
      style: Object.keys(inlineStyles).length > 0 ? inlineStyles : undefined
    }
  }, [options])

  return styles
}

/**
 * 에러 경계 컴포넌트를 위한 전용 스타일 Hook
 */
export function useErrorBoundaryStyles() {
  return {
    container: 'error-boundary-container',
    title: 'error-title',
    message: 'error-message',
    details: 'error-details',
    detailsContent: 'error-details-content',
    actions: 'error-actions',
    primaryButton: 'error-action-btn primary',
    secondaryButton: 'error-action-btn secondary'
  }
}

/**
 * 진행률 바를 위한 스타일 Hook
 */
export function useProgressStyles(variant: ColorVariant = 'primary', size: 'sm' | 'md' | 'lg' = 'md') {
  return useMemo(() => ({
    container: `progress-container ${size === 'lg' ? 'lg' : size === 'sm' ? '' : ''}`,
    bar: `progress-bar ${variant} animated`
  }), [variant, size])
}

/**
 * 카드 컴포넌트를 위한 스타일 Hook
 */
export function useCardStyles(options: {
  interactive?: boolean
  size?: 'sm' | 'md' | 'lg'
  hover?: boolean
} = {}) {
  return useMemo(() => {
    const classNames = ['card']
    
    if (options.interactive) {
      classNames.push('card-interactive')
    }
    
    if (options.size && options.size !== 'md') {
      classNames.push(`card-${options.size}`)
    }
    
    if (options.hover) {
      classNames.push('hover-lift', 'hover-shadow')
    }
    
    return {
      card: classNames.join(' '),
      header: 'card-header',
      body: 'card-body',
      footer: 'card-footer'
    }
  }, [options])
}

/**
 * 버튼을 위한 스타일 Hook
 */
export function useButtonStyles(
  variant: 'primary' | 'secondary' | 'outline' | 'ghost' | 'success' | 'warning' | 'error' = 'primary',
  size: 'sm' | 'md' | 'lg' | 'xl' = 'md'
) {
  return useMemo(() => {
    const classNames = ['btn', `btn-${variant}`]
    
    if (size !== 'md') {
      classNames.push(`btn-${size}`)
    }
    
    return classNames.join(' ')
  }, [variant, size])
}

/**
 * 폼 요소를 위한 스타일 Hook
 */
export function useFormStyles(options: {
  error?: boolean
  size?: 'sm' | 'md' | 'lg'
  required?: boolean
} = {}) {
  return useMemo(() => {
    const inputClasses = ['form-input']
    const labelClasses = ['form-label']
    
    if (options.error) {
      inputClasses.push('error', 'focus-ring-error')
    } else {
      inputClasses.push('focus-ring')
    }
    
    if (options.size && options.size !== 'md') {
      inputClasses.push(`form-input-${options.size}`)
    }
    
    if (options.required) {
      labelClasses.push('required')
    }
    
    return {
      group: 'form-group',
      label: labelClasses.join(' '),
      input: inputClasses.join(' '),
      help: 'form-help',
      error: 'form-error'
    }
  }, [options])
}

/**
 * 배지를 위한 스타일 Hook
 */
export function useBadgeStyles(
  variant: ColorVariant | 'critical' | 'high' | 'medium' | 'low' = 'primary',
  size: 'sm' | 'md' | 'lg' = 'md'
) {
  return useMemo(() => {
    const classNames = ['badge', `badge-${variant}`]
    
    if (size !== 'md') {
      classNames.push(`badge-${size}`)
    }
    
    return classNames.join(' ')
  }, [variant, size])
}

/**
 * 모달을 위한 스타일 Hook
 */
export function useModalStyles(size: 'sm' | 'md' | 'lg' | 'xl' = 'md') {
  return useMemo(() => ({
    backdrop: 'modal-backdrop',
    modal: `modal modal-${size}`,
    header: 'modal-header',
    title: 'modal-title',
    close: 'modal-close',
    body: 'modal-body',
    footer: 'modal-footer'
  }), [size])
}

/**
 * 레이아웃을 위한 유틸리티 Hook
 */
export function useLayoutStyles() {
  return {
    centerContainer: (size: 'sm' | 'md' | 'lg' | 'xl' | 'full' = 'lg') => `center-container ${size !== 'lg' ? size : ''}`,
    flexCenter: 'flex-center',
    flexBetween: 'flex-between',
    flexStart: 'flex-start',
    flexEnd: 'flex-end',
    flexColCenter: 'flex-col-center'
  }
}

/**
 * 애니메이션을 위한 Hook
 */
export function useAnimationStyles() {
  return {
    fadeIn: 'animate-fade-in',
    fadeInUp: 'animate-fade-in-up',
    slideIn: 'animate-slide-in',
    pulse: 'animate-pulse',
    spin: 'animate-spin'
  }
}

/**
 * 동적 차트 및 진행률 바를 위한 Hook
 */
export function useChartStyles() {
  return {
    // 언어별 색상 클래스 생성
    getLanguageColorClass: (language: string): string => {
      const normalizedLang = language.toLowerCase().replace(/[^a-z]/g, '')
      return `lang-color-${normalizedLang}`
    },
    
    // 차트 색상 클래스 생성 (인덱스 기반)
    getChartColorClass: (index: number): string => {
      return `chart-color-${index % 8}`
    },
    
    // 진행률 바 스타일
    progressBar: {
      container: 'bar-container',
      importance: 'bar-fill importance',
      complexity: 'bar-fill complexity',
      hotspot: 'bar-fill hotspot',
      centrality: 'bar-fill centrality'
    },
    
    // 메트릭 값 표시
    metricValue: 'metric-value',
    
    // 언어 색상 점
    languageColor: 'language-color',
    
    // 아이콘 마진
    iconWithMargin: 'icon-with-margin'
  }
}

/**
 * CSS 변수를 통한 동적 스타일 생성 Hook
 */
export function useDynamicStyles() {
  const setCustomProperty = useMemo(() => {
    return (element: HTMLElement, property: string, value: string) => {
      element.style.setProperty(property, value)
    }
  }, [])

  const createProgressBarStyle = useMemo(() => {
    return (percentage: number): React.CSSProperties => ({
      width: `${Math.max(0, Math.min(100, percentage))}%`
    })
  }, [])

  const createBackgroundColorStyle = useMemo(() => {
    return (color: string): React.CSSProperties => ({
      backgroundColor: color
    })
  }, [])

  const createColorStyle = useMemo(() => {
    return (color: string): React.CSSProperties => ({
      color: color
    })
  }, [])

  return {
    setCustomProperty,
    createProgressBarStyle,
    createBackgroundColorStyle,
    createColorStyle
  }
}