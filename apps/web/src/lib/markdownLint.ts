export interface LintIssue { code: string; message: string; severity: 'warn' | 'error'; line?: number }

// Very lightweight markdown/frontmatter linter for authoring UX
export function lintMarkdown(raw: string){
  const issues: LintIssue[] = [];
  const lines = raw.split(/\n/);
  // Title check (frontmatter title: ... )
  if(!/^---[\s\S]*?\n(?:title: ).*?\n[\s\S]*?---/.test(raw)){
    issues.push({ code:'frontmatter.title.missing', message:'Missing frontmatter title', severity:'error' });
  }
  // Objectives length
  const objMatch = raw.match(/objectives:\s*(.+)/);
  if(objMatch){
    const list = objMatch[1].split(',').map(s=>s.trim()).filter(Boolean);
    if(list.length > 10) issues.push({ code:'objectives.too_many', message:'Too many objectives (max 10)', severity:'warn' });
  }
  // Heading order (no skipping levels)
  let lastLevel = 0;
  lines.forEach((line,idx)=>{
    const hm = /^(#{1,6})\s+/.exec(line);
    if(hm){
      const lvl = hm[1].length;
      if(lastLevel && lvl > lastLevel + 1){
        issues.push({ code:'heading.skip_level', message:`Heading level jumps from ${lastLevel} to ${lvl}`, severity:'warn', line: idx+1 });
      }
      lastLevel = lvl;
    }
    if(/\s+$/.test(line) && line.trim().length){
      issues.push({ code:'trailing.space', message:'Trailing spaces', severity:'warn', line: idx+1 });
    }
    if(line.length > 140){
      issues.push({ code:'line.long', message:'Line exceeds 140 characters', severity:'warn', line: idx+1 });
    }
  });
  // Link extraction (simple)
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  const links: { text:string; url:string }[] = [];
  let lm: RegExpExecArray | null;
  while((lm = linkRegex.exec(raw))){ links.push({ text: lm[1], url: lm[2] }); }
  links.forEach(l=>{
    if(!/^https?:\/\//.test(l.url) && !l.url.startsWith('#') && !l.url.startsWith('./') && !l.url.startsWith('../')){
      issues.push({ code:'link.relative.unknown', message:`Suspicious link format: ${l.url}`, severity:'warn' });
    }
  });
  return issues;
}
