import { computeLineDiff } from '../lib/diff';

describe('computeLineDiff', () => {
  test('detects additions and deletions', () => {
    const oldText = 'a\nb\nc';
    const newText = 'a\nb\nX\nc';
    const diff = computeLineDiff(oldText, newText);
    const types = diff.map(d=>d.type+':'+d.text);
    expect(types).toContain('add:X');
    expect(types.filter(t=>t==='ctx:a').length).toBeGreaterThan(0);
  });

  test('all deleted', () => {
    const diff = computeLineDiff('one\ntwo', '');
    expect(diff.every(d=>d.type!=='add')).toBe(true);
    expect(diff.some(d=>d.type==='del')).toBe(true);
  });
});
