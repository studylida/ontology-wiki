import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Citation } from '../../types/contracts';
import { citationIndex, safeUrl } from '../../services/citationService';

type MarkdownNode = {type: string; value?: string; url?: string; children?: MarkdownNode[]};
function citationPlugin(citations: Map<string, Citation>) {
  return () => (tree: MarkdownNode) => {
    const walk = (node: MarkdownNode) => {
      if (!node.children || ['link', 'code', 'inlineCode', 'html'].includes(node.type)) return;
      const children: MarkdownNode[] = [];
      for (const child of node.children) {
        if (child.type === 'text' && child.value) {
          const pattern = /\[\[([^\]\n]+)\]\]/g;
          let last = 0, match: RegExpExecArray | null;
          while ((match = pattern.exec(child.value))) {
            if (!citations.has(match[1])) continue;
            children.push({type: 'text', value: child.value.slice(last, match.index)});
            children.push({type: 'link', url: `citation:${encodeURIComponent(match[1])}`, children: [{type: 'text', value: match[1]}]});
            last = match.index + match[0].length;
          }
          children.push({type: 'text', value: child.value.slice(last)});
        } else { walk(child); children.push(child); }
      }
      node.children = children;
    };
    walk(tree);
  };
}
export function SafeMarkdown({content, citations = [], onCitation}: {content: string; citations?: Citation[]; onCitation?: (citation: Citation) => void}) {
  const index = useMemo(() => citationIndex(citations), [citations]);
  const plugin = useMemo(() => citationPlugin(index), [index]);
  return <div className="markdown"><ReactMarkdown skipHtml remarkPlugins={[remarkGfm, plugin]}
    urlTransform={url => url.startsWith('citation:') ? url : safeUrl(url) || ''}
    components={{img: () => null, a: ({href, children}) => {
      if (href?.startsWith('citation:')) {
        let key = ''; try { key = decodeURIComponent(href.slice(9)); } catch { /* Inert malformed reference. */ }
        const citation = index.get(key);
        return citation && onCitation ? <button className="inline-citation" title={citation.title}
          aria-label={`출처 ${citation.number}: ${citation.title}`} onClick={() => onCitation(citation)}>{citation.number}</button> : <span>{children}</span>;
      }
      const url = safeUrl(href);
      return url ? <a href={url} target="_blank" rel="noopener noreferrer">{children}</a> : <span>{children}</span>;
    }, table: ({children}) => <div className="table-scroll"><table>{children}</table></div>}}>{content}</ReactMarkdown></div>;
}
export function DocumentMarkdown({content}: {content: string}) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(content);
  if (!match) return <SafeMarkdown content={content} />;
  return <><details><summary>파일에 기록된 메타데이터</summary><p>원문의 기록이며 공식성·정확성 검증이 아닙니다.</p><pre>{match[1]}</pre></details><SafeMarkdown content={content.slice(match[0].length)} /></>;
}
