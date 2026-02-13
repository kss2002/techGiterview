type ReportHandler = (metric: unknown) => void

const reportWebVitals = (_onPerfEntry?: ReportHandler) => {
  // web-vitals 패키지를 사용하지 않는 구성에서는 no-op 처리
}

export default reportWebVitals
