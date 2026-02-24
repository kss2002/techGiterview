export type AIProviderType = 'upstage' | 'gemini'

export const API_STORAGE_KEYS = {
  GITHUB_TOKEN: 'techgiterview_github_token',
  GOOGLE_API_KEY: 'techgiterview_google_api_key',
  UPSTAGE_API_KEY: 'techgiterview_upstage_api_key',
  SELECTED_AI_PROVIDER: 'techgiterview_selected_ai_provider',
} as const

export interface StoredApiKeys {
  githubToken: string
  googleApiKey: string
  upstageApiKey: string
  selectedProvider: AIProviderType
}

const normalizeProvider = (provider?: string | null): AIProviderType =>
  provider === 'gemini' || provider === 'google' ? 'gemini' : 'upstage'

export const getProviderFromSelectedAI = (
  selectedAI?: string | null,
  fallbackProvider?: string | null
): AIProviderType => {
  const normalized = (selectedAI || '').toLowerCase()

  if (normalized.includes('gemini') || normalized.includes('google')) {
    return 'gemini'
  }

  if (normalized.includes('upstage') || normalized.includes('solar')) {
    return 'upstage'
  }

  return normalizeProvider(fallbackProvider)
}

export const getApiKeysFromStorage = (): StoredApiKeys => {
  try {
    return {
      githubToken: localStorage.getItem(API_STORAGE_KEYS.GITHUB_TOKEN) || '',
      googleApiKey: localStorage.getItem(API_STORAGE_KEYS.GOOGLE_API_KEY) || '',
      upstageApiKey: localStorage.getItem(API_STORAGE_KEYS.UPSTAGE_API_KEY) || '',
      selectedProvider: normalizeProvider(
        localStorage.getItem(API_STORAGE_KEYS.SELECTED_AI_PROVIDER)
      ),
    }
  } catch (error) {
    return {
      githubToken: '',
      googleApiKey: '',
      upstageApiKey: '',
      selectedProvider: 'upstage',
    }
  }
}

interface CreateApiHeadersOptions {
  includeApiKeys?: boolean
  selectedAI?: string
  provider?: AIProviderType
  apiKeys?: Partial<StoredApiKeys>
}

export const createApiHeaders = (
  includeApiKeysOrOptions: boolean | CreateApiHeadersOptions = false
): Record<string, string> => {
  const options: CreateApiHeadersOptions =
    typeof includeApiKeysOrOptions === 'boolean'
      ? { includeApiKeys: includeApiKeysOrOptions }
      : includeApiKeysOrOptions

  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  }

  if (!options.includeApiKeys) {
    return headers
  }

  const stored = getApiKeysFromStorage()
  const mergedKeys: StoredApiKeys = {
    ...stored,
    ...options.apiKeys,
    selectedProvider: normalizeProvider(
      options.apiKeys?.selectedProvider || stored.selectedProvider
    ),
  }

  if (mergedKeys.githubToken) {
    headers['X-GitHub-Token'] = mergedKeys.githubToken
  }

  const resolvedProvider =
    options.provider ??
    getProviderFromSelectedAI(options.selectedAI, mergedKeys.selectedProvider)

  if (resolvedProvider === 'gemini') {
    if (mergedKeys.googleApiKey) {
      headers['X-Google-API-Key'] = mergedKeys.googleApiKey
    }
  } else if (mergedKeys.upstageApiKey) {
    headers['X-Upstage-API-Key'] = mergedKeys.upstageApiKey
  }

  return headers
}

export const hasRequiredApiKeys = (
  selectedAI?: string,
  provider?: AIProviderType
): boolean => {
  const keys = getApiKeysFromStorage()
  if (!keys.githubToken) return false

  const resolvedProvider =
    provider ?? getProviderFromSelectedAI(selectedAI, keys.selectedProvider)

  return resolvedProvider === 'gemini'
    ? !!keys.googleApiKey
    : !!keys.upstageApiKey
}
