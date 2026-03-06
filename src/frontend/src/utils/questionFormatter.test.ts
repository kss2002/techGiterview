import { buildQuestionPreviewText, formatQuestionForDisplay, stripMarkdownForPreview } from './questionFormatter'

describe('questionFormatter preview helpers', () => {
  it('strips markdown syntax for readable preview text', () => {
    const raw = '**질문:** `package.json`에서 [dependencies](https://example.com)를 설명하고 - 장단점을 말해주세요.'
    const plain = stripMarkdownForPreview(raw)

    expect(plain).toContain('질문:')
    expect(plain).toContain('package.json')
    expect(plain).toContain('dependencies')
    expect(plain).not.toContain('**')
    expect(plain).not.toContain('`')
    expect(plain).not.toContain('[')
    expect(plain).not.toContain(']')
  })

  it('builds truncated preview text from structured question payload', () => {
    const preview = buildQuestionPreviewText(
      {
        question: '**질문:** "package.json"에서 dependencies와 devDependencies 차이를 설명해보세요.',
        question_details_markdown: '**상황:** monorepo 환경에서 npm workspaces를 사용합니다.'
      },
      32
    )

    expect(preview.length).toBeLessThanOrEqual(35)
    expect(preview).toMatch(/dependencies/i)
    expect(preview).toContain('...')
  })

  it('normalizes question headline by stripping markdown question labels', () => {
    const formatted = formatQuestionForDisplay({
      question: '**질문:** `package.json`에서 dependencies와 devDependencies 차이를 설명해보세요.'
    })

    expect(formatted.headline).toContain('package.json')
    expect(formatted.headline).not.toContain('**')
    expect(formatted.headline).not.toMatch(/^질문[:：]/)
  })
})
