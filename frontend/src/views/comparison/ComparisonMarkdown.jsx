import React from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export const evidenceAnchor = id => `comparison-evidence-${encodeURIComponent(id)}`;
export const evidenceHref = id => `#${encodeURIComponent(evidenceAnchor(id))}`;
export function openEvidence(event, id) {
  event.preventDefault(); // The app uses the URL hash to select its tab.
  const entry = document.getElementById(evidenceAnchor(id));
  const details = entry?.closest('details');
  if (details) details.open = true;
  entry?.scrollIntoView({block: 'center'});
}

export function ComparisonMarkdown({children, evidences = []}) {
  const known = new Set(evidences.map(e => e.id));
  function citations() {
    return tree => {
      function visit(node) {
        if (!node.children || ['link', 'code', 'inlineCode', 'html'].includes(node.type)) return;
        node.children = node.children.flatMap(child => {
          if (child.type !== 'text') {visit(child); return [child];}
          const parts = []; let cursor = 0;
          for (const match of child.value.matchAll(/\[([^\]\n]+)\]/g)) {
            if (!known.has(match[1])) continue;
            if (match.index > cursor) parts.push({type: 'text', value: child.value.slice(cursor, match.index)});
            parts.push({type: 'link', url: evidenceHref(match[1]), children: [{type: 'text', value: match[0]}]});
            cursor = match.index + match[0].length;
          }
          return parts.length ? [...parts, {type: 'text', value: child.value.slice(cursor)}] : [child];
        });
      }
      visit(tree);
    };
  }
  return <div className="comparison-markdown"><Markdown remarkPlugins={[remarkGfm, citations]} skipHtml
    urlTransform={url => /^https?:\/\//i.test(url) || [...known].some(id => evidenceHref(id) === url) ? url : undefined}
    components={{img: () => null, a: ({node, href, children}) => <a href={href}
      target={href?.startsWith('http') ? '_blank' : undefined} rel="noopener noreferrer"
      onClick={event => {const id = [...known].find(id => evidenceHref(id) === href);
        if (id) openEvidence(event, id);
      }}>{children}</a>}}>{String(children || '')}</Markdown></div>;
}
