#!/usr/bin/env node

import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

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

const allowSelector = (selector, prefixes) => {
  if (!selector) return true
  if (selector.startsWith('@')) return true
  if (/^(from|to|\d+%)$/.test(selector)) return true
  return prefixes.some((prefix) => selector.startsWith(prefix))
}

const violations = []

for (const rule of scopeRules) {
  const absPath = resolve(process.cwd(), rule.file)
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
  const lines = content.split('\n')

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i]
    const trimmed = line.trim()

    if (!trimmed || trimmed.startsWith('/*') || trimmed.startsWith('*') || trimmed.startsWith('*/')) {
      continue
    }

    const braceIndex = trimmed.indexOf('{')
    if (braceIndex < 0) continue

    const selectorPart = trimmed.slice(0, braceIndex).trim()
    if (!selectorPart) continue

    const selectors = selectorPart.split(',').map((s) => s.trim()).filter(Boolean)

    for (const selector of selectors) {
      if (!allowSelector(selector, rule.prefixes)) {
        violations.push({
          file: rule.file,
          line: i + 1,
          selector,
          reason: `Selector must start with one of: ${rule.prefixes.join(', ')}`,
        })
      }
    }
  }
}

if (violations.length > 0) {
  console.error('CSS scope check failed:')
  for (const violation of violations) {
    console.error(
      `- ${violation.file}:${violation.line} :: ${violation.selector} (${violation.reason})`
    )
  }
  process.exit(1)
}

console.log('CSS scope check passed.')
