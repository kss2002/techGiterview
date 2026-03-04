export type ReportHandler = (metric: unknown) => void

// Optional performance hook. Kept as a no-op until web-vitals is reintroduced.
const reportWebVitals = (_onPerfEntry?: ReportHandler) => {}

export default reportWebVitals
