#!/usr/bin/env node

import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { relative, resolve } from 'node:path'

const projectRoot = process.cwd()

const scopeRules = [
  {
    file: 'src/pages/HomePage.css',
    prefixes: ['.home-page-v2', '.home-v2'],
  },
  {
    file: 'src/pages/InterviewPage.css',
    prefixes: ['.interview-page'],
  },
  {
    file: 'src/pages/ReportsPage.css',
    prefixes: ['.reports-page'],
  },
  {
    file: 'src/pages/DashboardPage-CLEAN.css',
    prefixes: ['.dashboard-legacy-page'],
  },
]

const criticalSelectorRules = [
  {
    file: 'src/pages/InterviewPage.css',
    selector: '.interview-page .finish-interview-btn',
    maxOccurrences: 1,
  },
]

const allowedV2ImportFiles = new Set(['src/index.css'])
const createImportV2Pattern = () => /@import\s+(?:url\()?\s*['"][^'"]*\/?v2\.css['"]\s*\)?\s*;/gi

const toPosixPath = (filePath) => relative(projectRoot, filePath).split('\\').join('/')

const countLineAt = (content, index) => content.slice(0, index).split('\n').length

const stripComments = (content) => content.replace(/\/\*[\s\S]*?\*\//g, '')

const parseSelectorEntries = (content) => {
  const normalizedContent = stripComments(content)
  const entries = []
  let braceDepth = 0
  let statementStart = 0

  for (let index = 0; index < normalizedContent.length; index += 1) {
    const char = normalizedContent[index]

    if (char === ';' && braceDepth > 0) {
      statementStart = index + 1
      continue
    }

    if (char === '}') {
      braceDepth = Math.max(0, braceDepth - 1)
      statementStart = index + 1
      continue
    }

    if (char === '{') {
      const selectorText = normalizedContent.slice(statementStart, index).trim()
      if (selectorText) {
        entries.push({
          selectorText,
          line: countLineAt(normalizedContent, statementStart),
        })
      }
      braceDepth += 1
      statementStart = index + 1
    }
  }

  return entries
}

const splitSelectors = (selectorText) =>
  selectorText
    .split(',')
    .map((value) => value.replace(/\s+/g, ' ').trim())
    .filter(Boolean)

const allowSelector = (selector, prefixes) => {
  if (!selector) return true
  if (selector.startsWith('@')) return true
  if (/^(from|to|\d+%)$/.test(selector)) return true
  return prefixes.some((prefix) => selector.startsWith(prefix))
}

const listCssFiles = (rootDir) => {
  if (!existsSync(rootDir)) return []
  const stack = [rootDir]
  const files = []

  while (stack.length > 0) {
    const current = stack.pop()
    if (!current) continue

    const entries = readdirSync(current, { withFileTypes: true })
    for (const entry of entries) {
      const absPath = resolve(current, entry.name)
      if (entry.isDirectory()) {
        stack.push(absPath)
        continue
      }
      if (entry.isFile() && absPath.endsWith('.css')) {
        files.push(absPath)
      }
    }
  }

  return files
}

const violations = []

for (const rule of scopeRules) {
  const absPath = resolve(projectRoot, rule.file)
  if (!existsSync(absPath)) {
    violations.push({
      file: rule.file,
      line: 0,
      selector: '<missing file>',
      reason: 'File not found',
    })
    continue
  }

  const content = readFileSync(absPath, 'utf8')
  const selectorEntries = parseSelectorEntries(content)

  for (const entry of selectorEntries) {
    const selectors = splitSelectors(entry.selectorText)
    for (const selector of selectors) {
      if (!allowSelector(selector, rule.prefixes)) {
        violations.push({
          file: rule.file,
          line: entry.line,
          selector,
          reason: `Selector must start with one of: ${rule.prefixes.join(', ')}`,
        })
      }
    }
  }
}

for (const selectorRule of criticalSelectorRules) {
  const absPath = resolve(projectRoot, selectorRule.file)
  if (!existsSync(absPath)) continue

  const content = readFileSync(absPath, 'utf8')
  const selectorEntries = parseSelectorEntries(content)

  let count = 0
  selectorEntries.forEach((entry) => {
    const selectors = splitSelectors(entry.selectorText)
    selectors.forEach((selector) => {
      if (selector === selectorRule.selector) {
        count += 1
      }
    })
  })

  if (count > selectorRule.maxOccurrences) {
    violations.push({
      file: selectorRule.file,
      line: 0,
      selector: selectorRule.selector,
      reason: `Selector duplicated ${count} times (max ${selectorRule.maxOccurrences})`,
    })
  }
}

const cssFiles = listCssFiles(resolve(projectRoot, 'src'))
for (const cssFile of cssFiles) {
  const relPath = toPosixPath(cssFile)
  const content = readFileSync(cssFile, 'utf8')
  const importV2Pattern = createImportV2Pattern()

  let match
  while ((match = importV2Pattern.exec(content)) !== null) {
    if (allowedV2ImportFiles.has(relPath)) {
      continue
    }

    violations.push({
      file: relPath,
      line: countLineAt(content, match.index),
      selector: match[0],
      reason: 'v2.css must only be imported from src/index.css',
    })
  }
}

const indexCssPath = resolve(projectRoot, 'src/index.css')
if (existsSync(indexCssPath)) {
  const indexContent = readFileSync(indexCssPath, 'utf8')
  const importV2Pattern = createImportV2Pattern()
  const matches = [...indexContent.matchAll(importV2Pattern)]
  if (matches.length !== 1) {
    violations.push({
      file: 'src/index.css',
      line: 1,
      selector: '@import ... v2.css',
      reason: `Expected exactly one v2.css import in src/index.css (found ${matches.length})`,
    })
  }
}

if (violations.length > 0) {
  console.error('CSS scope check failed:')
  for (const violation of violations) {
    console.error(`- ${violation.file}:${violation.line} :: ${violation.selector} (${violation.reason})`)
  }
  process.exit(1)
}

console.log('CSS scope check passed.')
