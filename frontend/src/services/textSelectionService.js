// Only returns visible-text offsets; explanation requests keep the selected spelling.
export function createSelectionMatcher(terms) {
  const names = [...new Set(terms.filter((term) => typeof term === 'string' && term.length))]
    .sort((a, b) => b.length - a.length);
  const pattern = names.length ? new RegExp(names.map((name) => name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'giu') : null;
  const word = /[\p{L}\p{N}_]/u;
  const particles = ['으로', '에서', '에게', '한테', '께서', '이랑', '이라는', '이라고', '이라면', '처럼', '보다', '조차', '마저', '밖에', '부터', '까지', '은', '는', '이', '가', '을', '를', '의', '에', '로', '와', '과', '도', '만', '랑'].sort((a, b) => b.length - a.length);
  return (text, offset) => {
    if (!pattern) return null;
    pattern.lastIndex = 0;
    let match;
    while ((match = pattern.exec(text))) {
      const start = match.index;
      const end = start + match[0].length;
      if (start > offset) break;
      if (start && word.test(text[start - 1])) continue;
      const tail = text.slice(end).match(/^[\p{L}\p{N}_]*/u)[0];
      let suffix = tail;
      while (suffix) {
        const particle = particles.find((item) => suffix.startsWith(item));
        if (!particle) break;
        suffix = suffix.slice(particle.length);
      }
      if (!suffix && offset <= end + tail.length) return { start, end };
    }
    return null;
  };
}
