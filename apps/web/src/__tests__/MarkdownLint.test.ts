import { lintMarkdown } from '../lib/markdownLint';

describe('markdown lint', () => {
  test('detects missing title', () => {
    const issues = lintMarkdown('---\nobjectives: a\n---\n# H');
    expect(issues.find(i=>i.code==='frontmatter.title.missing')).toBeTruthy();
  });
  test('flags heading jump', () => {
    const issues = lintMarkdown('---\ntitle: T\n---\n# H1\n### H3');
    expect(issues.find(i=>i.code==='heading.skip_level')).toBeTruthy();
  });
});
