/**
 * 인터뷰 페이지 높이 매칭 유틸리티
 * answer-item과 input-container의 시작 위치를 동일하게 맞춤
 */

import React from 'react';

export interface HeightMatchingOptions {
  answerSelector?: string;
  inputHeaderSelector?: string;
  debounceMs?: number;
  enableVisualFeedback?: boolean;
}

export class HeightMatcher {
  private answerSelector: string;
  private inputHeaderSelector: string;
  private debounceMs: number;
  private enableVisualFeedback: boolean;
  private resizeObserver?: ResizeObserver;
  private mutationObserver?: MutationObserver;
  private debounceTimer?: NodeJS.Timeout;

  constructor(options: HeightMatchingOptions = {}) {
    this.answerSelector = options.answerSelector || '.answer-item';
    this.inputHeaderSelector = options.inputHeaderSelector || '.input-header';
    this.debounceMs = options.debounceMs || 150;
    this.enableVisualFeedback = options.enableVisualFeedback ?? true;
  }

  /**
   * 높이 매칭 시작
   */
  public start(): void {
    this.setupObservers();
    this.matchHeights();
  }

  /**
   * 높이 매칭 중지 및 정리
   */
  public destroy(): void {
    this.resizeObserver?.disconnect();
    this.mutationObserver?.disconnect();
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.resetInputHeader();
  }

  /**
   * 즉시 높이 매칭 실행
   */
  public matchHeights(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }

    this.debounceTimer = setTimeout(() => {
      this.performHeightMatching();
    }, this.debounceMs);
  }

  private setupObservers(): void {
    // ResizeObserver로 레이아웃 변경 감지
    this.resizeObserver = new ResizeObserver(() => {
      this.matchHeights();
    });

    // MutationObserver로 DOM 변경 감지
    this.mutationObserver = new MutationObserver((mutations) => {
      const shouldUpdate = mutations.some(mutation => 
        mutation.type === 'childList' || 
        (mutation.type === 'attributes' && 
         (mutation.attributeName === 'class' || mutation.attributeName === 'style'))
      );

      if (shouldUpdate) {
        this.matchHeights();
      }
    });

    // 관찰 시작
    const interviewContent = document.querySelector('.interview-content');
    if (interviewContent) {
      this.resizeObserver.observe(interviewContent);
      this.mutationObserver.observe(interviewContent, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class', 'style']
      });
    }
  }

  private performHeightMatching(): void {
    const answerItem = document.querySelector(this.answerSelector) as HTMLElement;
    const inputHeader = document.querySelector(this.inputHeaderSelector) as HTMLElement;

    if (!answerItem || !inputHeader) {
      // answer-item이 없으면 기본 스타일로 복원
      this.resetInputHeader();
      return;
    }

    // 시각적 피드백 시작
    if (this.enableVisualFeedback) {
      inputHeader.classList.add('height-matching');
    }

    // answer-item의 정확한 위치 계산
    const answerRect = answerItem.getBoundingClientRect();
    const answerComputedStyle = window.getComputedStyle(answerItem);
    const answerPaddingTop = parseFloat(answerComputedStyle.paddingTop);
    
    // input-header의 현재 위치 계산
    const inputRect = inputHeader.getBoundingClientRect();
    const inputParent = inputHeader.parentElement?.getBoundingClientRect();
    
    if (!inputParent) return;

    // 높이 차이 계산
    const answerStartY = answerRect.top + answerPaddingTop;
    const inputStartY = inputRect.top;
    const heightDifference = answerStartY - inputStartY;

    // CSS 변수로 높이 설정
    const inputHeaderHeight = answerRect.height;
    const adjustedPaddingTop = Math.max(answerPaddingTop, 12); // 최소 패딩 보장

    inputHeader.style.setProperty('--matched-height', `${inputHeaderHeight}px`);
    inputHeader.style.setProperty('--matched-padding-top', `${adjustedPaddingTop}px`);
    inputHeader.style.setProperty('--matched-padding-bottom', `${adjustedPaddingTop}px`);

    // 매칭 클래스 적용
    inputHeader.classList.add('height-matched');

    // 시각적 피드백 완료
    setTimeout(() => {
      if (this.enableVisualFeedback) {
        inputHeader.classList.remove('height-matching');
      }
    }, 500);

    console.log('Height matching applied:', {
      answerHeight: answerRect.height,
      adjustedPaddingTop,
      heightDifference
    });
  }

  private resetInputHeader(): void {
    const inputHeader = document.querySelector(this.inputHeaderSelector) as HTMLElement;
    if (!inputHeader) return;

    // CSS 변수 제거
    inputHeader.style.removeProperty('--matched-height');
    inputHeader.style.removeProperty('--matched-padding-top');
    inputHeader.style.removeProperty('--matched-padding-bottom');

    // 클래스 제거
    inputHeader.classList.remove('height-matched', 'height-matching');
  }
}

/**
 * 간편한 높이 매칭 시작 함수
 */
export function startHeightMatching(options?: HeightMatchingOptions): HeightMatcher {
  const matcher = new HeightMatcher(options);
  matcher.start();
  return matcher;
}

/**
 * React Hook으로 사용할 수 있는 높이 매칭
 */
export function useHeightMatching(options?: HeightMatchingOptions) {
  const matcherRef = React.useRef<HeightMatcher | null>(null);

  React.useEffect(() => {
    matcherRef.current = new HeightMatcher(options);
    matcherRef.current.start();

    return () => {
      matcherRef.current?.destroy();
    };
  }, []);

  const manualMatch = React.useCallback(() => {
    matcherRef.current?.matchHeights();
  }, []);

  return { manualMatch };
}