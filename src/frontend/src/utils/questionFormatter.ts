export interface QuestionFormatSource {
  question?: string | null
  question_headline?: string | null
  question_details_markdown?: string | null
  question_has_details?: boolean | null
}

export interface FormattedQuestion {
  headline: string
  detailsMarkdown: string
  hasDetails: boolean
  normalizedQuestion: string
}

const SECTION_LABELS = [
  '질문',
  '상황',
  '요구사항',
  '평가 포인트',
  '추가 질문 포인트',
] as const

const normalizeInlineSpaces = (value: string): string =>
  value.replace(/\s+/g, ' ').trim()

const decodeHtmlEntities = (value: string): string =>
  value
    .replace(/&nbsp;/gi, ' ')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&amp;/gi, '&')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")

const stripOuterQuestionWrapperHtml = (value: string): string => {
  let current = value.trim()
  const wrapperPattern =
    /^\s*<div[^>]*class=["'][^"']*\bquestion-text\b[^"']*["'][^>]*>([\s\S]*)<\/div>\s*$/i

  while (wrapperPattern.test(current)) {
    current = current.replace(wrapperPattern, '$1').trim()
  }

  return current
}

const convertQuestionHtmlToMarkdown = (value: string): string => {
  let converted = value

  SECTION_LABELS.forEach((label) => {
    const labelPattern = new RegExp(
      `<(?:strong|b)>\\s*${label}\\s*[:：]\\s*<\\/(?:strong|b)>`,
      'gi'
    )
    converted = converted.replace(labelPattern, `**${label}:** `)
  })

  converted = converted
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p\s*>/gi, '\n')
    .replace(/<p[^>]*>/gi, '')
    .replace(/<\/li\s*>/gi, '\n')
    .replace(/<li[^>]*>/gi, '- ')
    .replace(/<\/div\s*>/gi, '\n')
    .replace(/<div[^>]*>/gi, '')
    .replace(/<[^>]+>/g, '')

  converted = decodeHtmlEntities(converted)
  converted = converted.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  converted = converted.replace(/\n{3,}/g, '\n\n')
  return converted.trim()
}

const dedupeMirroredText = (value: string): string => {
  const text = value.trim()
  if (text.length < 20) {
    return text
  }

  const repeatedBlockMatch = text.match(/^([\s\S]{200,}?)\s*\1$/)
  if (repeatedBlockMatch?.[1]) {
    return repeatedBlockMatch[1].trim()
  }

  if (text.length % 2 === 0) {
    const half = text.length / 2
    const first = text.slice(0, half).trim()
    const second = text.slice(half).trim()
    if (first && normalizeInlineSpaces(first) === normalizeInlineSpaces(second)) {
      return first
    }
  }

  return text
}

const canonicalize = (value: string): string =>
  normalizeInlineSpaces(value.replace(/[*_`>#-]/g, ' ')).toLowerCase()

const cleanSectionLine = (value: string): string => {
  let line = (value || '').trim()
  if (!line) return ''

  line = line.replace(/^\s*[-*+]\s*/, '')
  line = line.replace(/^\*\*+\s*/, '')
  line = line.replace(/\s*\*\*+$/, '')
  line = line.replace(/^\s*[:：]\s*/, '')
  return normalizeInlineSpaces(line)
}

const mergeSectionContents = (contents: string[]): string => {
  const lines: string[] = []
  const seen = new Set<string>()

  contents.forEach((content) => {
    content
      .split(/\n+/)
      .map((line) => cleanSectionLine(line))
      .filter(Boolean)
      .forEach((line) => {
        const key = canonicalize(line)
        if (!key || seen.has(key)) return
        seen.add(key)
        lines.push(line)
      })
  })

  if (lines.length === 0) return ''
  if (lines.length === 1) return lines[0]
  return lines.map((line) => `- ${line}`).join('\n')
}

const extractHeadline = (value: string): string => {
  const lines = value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  if (lines.length === 0) {
    return ''
  }

  const firstLine = lines[0].replace(/^[>\-\*\d\.\)\s]+/, '').trim()
  if (!firstLine) {
    return ''
  }

  const questionMarkIndex = firstLine.indexOf('?')
  if (questionMarkIndex !== -1 && questionMarkIndex < 180) {
    return firstLine.slice(0, questionMarkIndex + 1).trim()
  }

  return firstLine
}

const removeHeadlinePrefix = (fullText: string, headline: string): string => {
  if (!fullText || !headline) {
    return fullText.trim()
  }

  const trimmed = fullText.trim()
  if (trimmed.startsWith(headline)) {
    return trimmed.slice(headline.length).replace(/^[\s:-]+/, '').trim()
  }

  return trimmed
}

const parseStructuredSections = (value: string): FormattedQuestion | null => {
  const normalizedHeaders = value
    .replace(
      /\*\*\s*(질문|상황|요구사항|평가 포인트|추가 질문 포인트)\s*[:：]\s*\*\*/gi,
      '$1:'
    )
    .replace(
      /\*\*\s*(질문|상황|요구사항|평가 포인트|추가 질문 포인트)\s*\*\*\s*[:：]/gi,
      '$1:'
    )

  const spaced = normalizedHeaders
    .replace(
      /\s*((?:\*\*)?\s*(질문|상황|요구사항|평가 포인트|추가 질문 포인트)\s*(?:\*\*)?\s*[:：])/gi,
      '\n$1'
    )
    .replace(/\n{3,}/g, '\n\n')
    .trim()

  const sectionRegex =
    /^\s*(?:[-*]\s*)?(?:\*\*)?\s*(질문|상황|요구사항|평가 포인트|추가 질문 포인트)\s*(?:\*\*)?\s*[:：]\s*/gim
  const matches: Array<{ label: string; start: number; end: number }> = []

  let match: RegExpExecArray | null
  while ((match = sectionRegex.exec(spaced)) !== null) {
    matches.push({
      label: match[1],
      start: match.index,
      end: sectionRegex.lastIndex,
    })
  }

  if (matches.length === 0) {
    return null
  }

  const orderedSections: Array<{ label: string; content: string }> = []
  const seenSections = new Set<string>()

  matches.forEach((current, index) => {
    const contentStart = current.end
    const contentEnd = index + 1 < matches.length ? matches[index + 1].start : spaced.length
    const content = spaced.slice(contentStart, contentEnd).trim()
    if (!content) {
      return
    }

    const key = `${current.label}:${canonicalize(content)}`
    if (seenSections.has(key)) {
      return
    }

    seenSections.add(key)
    orderedSections.push({ label: current.label, content })
  })

  if (orderedSections.length === 0) {
    return null
  }

  const sectionMap = new Map<string, string[]>()
  const orderedLabels: string[] = []
  orderedSections.forEach((section) => {
    if (!sectionMap.has(section.label)) {
      sectionMap.set(section.label, [])
      orderedLabels.push(section.label)
    }
    sectionMap.get(section.label)!.push(section.content)
  })

  const mergedSections: Array<{ label: string; content: string }> = orderedLabels
    .map((label) => ({ label, content: mergeSectionContents(sectionMap.get(label) || []) }))
    .filter((section) => section.content)

  const questionSection =
    mergedSections.find((section) => section.label === '질문')?.content ?? ''
  const headlineSource = questionSection || mergedSections[0]?.content || orderedSections[0].content
  const headline = extractHeadline(headlineSource)

  const detailParts: string[] = []
  const questionRemainder = removeHeadlinePrefix(questionSection, headline)
  if (questionRemainder) {
    detailParts.push(`**질문 상세:**\n${questionRemainder}`)
  }

  mergedSections.forEach((section) => {
    if (section.label === '질문') {
      return
    }
    detailParts.push(`**${section.label}:**\n${section.content}`)
  })

  const detailsMarkdown = detailParts.join('\n\n').trim()
  const hasDetails = detailsMarkdown.length > 0
  const normalizedQuestion = hasDetails
    ? `${headline}\n\n${detailsMarkdown}`.trim()
    : headline

  return {
    headline,
    detailsMarkdown,
    hasDetails,
    normalizedQuestion,
  }
}

const parsePlainQuestion = (value: string): FormattedQuestion => {
  const paragraphs = value
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)

  const deduped: string[] = []
  const seen = new Set<string>()
  paragraphs.forEach((paragraph) => {
    const key = canonicalize(paragraph)
    if (!key || seen.has(key)) {
      return
    }
    seen.add(key)
    deduped.push(paragraph)
  })

  const merged = (deduped.join('\n\n').trim() || value).trim()
  const headline = extractHeadline(merged)
  const remainder = removeHeadlinePrefix(merged, headline)
  const hasDetails = remainder.length > 0 && canonicalize(remainder) !== canonicalize(headline)

  return {
    headline: headline || merged,
    detailsMarkdown: hasDetails ? remainder : '',
    hasDetails,
    normalizedQuestion: hasDetails
      ? `${headline}\n\n${remainder}`.trim()
      : (headline || merged),
  }
}

export const formatQuestionForDisplay = (
  source: QuestionFormatSource
): FormattedQuestion => {
  const backendHeadline = dedupeMirroredText(
    convertQuestionHtmlToMarkdown(stripOuterQuestionWrapperHtml(source.question_headline?.trim() ?? ''))
  )
  const backendDetails = dedupeMirroredText(
    convertQuestionHtmlToMarkdown(stripOuterQuestionWrapperHtml(source.question_details_markdown?.trim() ?? ''))
  )
  const backendHasDetails =
    source.question_has_details !== null && source.question_has_details !== undefined
      ? source.question_has_details
      : backendDetails.length > 0

  if (backendHeadline) {
    const parsedBackendDetails =
      backendDetails ? (parseStructuredSections(backendDetails) ?? parsePlainQuestion(backendDetails)) : null
    const normalizedDetails = parsedBackendDetails
      ? (parsedBackendDetails.hasDetails
        ? parsedBackendDetails.detailsMarkdown
        : parsedBackendDetails.normalizedQuestion)
      : ''
    const hasDetails = backendHasDetails && backendDetails.length > 0
    const normalizedQuestion = hasDetails
      ? `${backendHeadline}\n\n${normalizedDetails || backendDetails}`.trim()
      : backendHeadline

    return {
      headline: backendHeadline,
      detailsMarkdown: hasDetails ? (normalizedDetails || backendDetails) : '',
      hasDetails,
      normalizedQuestion,
    }
  }

  const rawQuestion = source.question?.trim() ?? ''
  if (!rawQuestion) {
    return {
      headline: '',
      detailsMarkdown: '',
      hasDetails: false,
      normalizedQuestion: '',
    }
  }

  const cleaned = dedupeMirroredText(
    convertQuestionHtmlToMarkdown(stripOuterQuestionWrapperHtml(rawQuestion))
  )

  return parseStructuredSections(cleaned) ?? parsePlainQuestion(cleaned)
}
