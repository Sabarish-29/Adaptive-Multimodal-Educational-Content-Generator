# Accessibility Checklist (WCAG 2.1 AA)

## UI
- Color contrast >= 4.5:1 (tokens enforced)
- Focus visible & logical order
- Skip to main content link
- Semantic landmarks (header, nav, main, footer)
- Keyboard operable components (no key traps)
- ARIA only when necessary; no redundant roles
- Live regions for dynamic recommendations (polite)
- Alt text for all non-decorative images
- Transcripts/captions for audio/video
- Plain-language variant for complex text
- Adjustable text size & line spacing controls
- Reduced motion preference respected

## Content Generation Gates
- Reading level within learner target ±1 grade
- Alt text presence & max length <= 160 chars
- Caption presence for media
- Toxicity score below threshold
- PII not detected (names, addresses, emails)
- Pedagogy rubric: objective alignment, clarity, scaffolding

## Testing
- Automated: eslint-plugin-jsx-a11y, axe-core CI run
- Manual: keyboard navigation pass, screen reader smoke (NVDA/VoiceOver)
- Regression: snapshot diffs for semantic HTML

## CI Enforcement
- If a11y gate fails -> fail build (except experimental feature branches with override flag)
