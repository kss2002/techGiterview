import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { HomePageNavbar } from './HomePageNavbar'

const providers = [
  {
    id: 'upstage-solar-pro3',
    name: 'Upstage Solar Pro3 (기본)',
    model: 'solar-pro3',
    status: 'ready',
    recommended: true,
  },
  {
    id: 'gemini-flash',
    name: 'Google Gemini 2.0 Flash',
    model: 'gemini-2.0-flash',
    status: 'ready',
    recommended: false,
  },
]

describe('HomePageNavbar', () => {
  it('renders selected provider and keeps provider order in dropdown', async () => {
    const user = userEvent.setup()
    const onSelectedAIChange = vi.fn()

    const { container } = render(
      <HomePageNavbar
        onShowApiKeySetup={vi.fn()}
        needsApiKeySetup={false}
        isConnected={true}
        providers={providers}
        selectedAI="upstage-solar-pro3"
        onSelectedAIChange={onSelectedAIChange}
      />
    )

    expect(screen.getByText('Upstage Solar Pro3 (기본)')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Upstage Solar Pro3/ }))

    const providerNames = Array.from(container.querySelectorAll('.navbar-dropdown-item-name')).map((el) =>
      el.textContent?.trim() ?? ''
    )

    expect(providerNames[0]).toContain('Upstage Solar Pro3 (기본)')
    expect(providerNames[1]).toContain('Google Gemini 2.0 Flash')

    const geminiButton = screen.getByRole('button', { name: /Google Gemini 2.0 Flash/i })
    await user.click(geminiButton)

    expect(onSelectedAIChange).toHaveBeenCalledWith('gemini-flash')
  })

  it('shows warning label when API setup is required', () => {
    render(
      <HomePageNavbar
        onShowApiKeySetup={vi.fn()}
        needsApiKeySetup={true}
        isConnected={false}
        providers={providers}
        selectedAI="upstage-solar-pro3"
        onSelectedAIChange={vi.fn()}
      />
    )

    expect(screen.getByText('API 설정 필요')).toBeInTheDocument()
  })
})
