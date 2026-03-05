import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { SampleRepositoriesSection } from './SampleRepositoriesSection'
import { SAMPLE_REPOSITORIES } from '../../constants/sampleRepos'

describe('SampleRepositoriesSection', () => {
  it('calls hover callbacks and select callback for sample chips', async () => {
    const user = userEvent.setup()
    const onRepoSelect = vi.fn()
    const onRepoHoverStart = vi.fn()
    const onRepoHoverEnd = vi.fn()

    render(
      <SampleRepositoriesSection
        onRepoSelect={onRepoSelect}
        onRepoHoverStart={onRepoHoverStart}
        onRepoHoverEnd={onRepoHoverEnd}
        isAnalyzing={false}
      />
    )

    const firstChip = screen.getAllByRole('button')[0]
    const expectedRepo = SAMPLE_REPOSITORIES[0]

    await user.hover(firstChip)
    expect(onRepoHoverStart).toHaveBeenCalledWith(expectedRepo)

    await user.unhover(firstChip)
    expect(onRepoHoverEnd).toHaveBeenCalled()

    await user.click(firstChip)
    expect(onRepoSelect).toHaveBeenCalledWith(expectedRepo)
  })
})
