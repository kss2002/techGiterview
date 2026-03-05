import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'

vi.mock('@pages/HomePage', () => ({
  HomePage: () => <div className="home-page-v2 v2-root v2-tone-709">HomePage Mock</div>
}))

import App from './App'

describe('App', () => {
  it('renders home entry title', async () => {
    render(<App />)
    expect(await screen.findByText('HomePage Mock')).toBeInTheDocument()
  })

  it('applies stitch 709 tone class on home root', async () => {
    render(<App />)
    const homeRoot = await screen.findByText('HomePage Mock')
    expect(homeRoot).toHaveClass('v2-tone-709')
  })
})
