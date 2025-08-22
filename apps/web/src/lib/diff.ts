export type DiffSegment = { type: 'ctx' | 'add' | 'del'; text: string };

// Simple line-based LCS diff for snapshot comparison
export function computeLineDiff(oldText: string, newText: string): DiffSegment[] {
  const o = oldText.split(/\r?\n/);
  const n = newText.split(/\r?\n/);
  const dp: number[][] = Array(o.length + 1).fill(0).map(() => Array(n.length + 1).fill(0));
  for (let i = 1; i <= o.length; i++) {
    for (let j = 1; j <= n.length; j++) {
      dp[i][j] = o[i - 1] === n[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  const out: DiffSegment[] = [];
  let i = o.length, j = n.length;
  while (i > 0 && j > 0) {
    if (o[i - 1] === n[j - 1]) { out.push({ type:'ctx', text:o[i - 1] }); i--; j--; }
    else if (dp[i - 1][j] >= dp[i][j - 1]) { out.push({ type:'del', text:o[i - 1] }); i--; }
    else { out.push({ type:'add', text:n[j - 1] }); j--; }
  }
  while(i>0) out.push({ type:'del', text:o[--i] });
  while(j>0) out.push({ type:'add', text:n[--j] }); // only adds if new has extra trailing lines
  return out.reverse().filter(s => !(s.type==='add' && s.text===''));
}
