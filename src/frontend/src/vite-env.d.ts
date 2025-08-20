/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_LOG_LEVEL: string
  readonly VITE_DEBUG_RENDER: string
  readonly VITE_DEBUG_PERFORMANCE: string
  readonly VITE_DEBUG_NETWORK: string
  readonly VITE_ENABLE_DEVTOOLS: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}