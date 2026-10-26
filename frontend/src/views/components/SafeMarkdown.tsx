import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Citation } from "../../types/contracts";
import { safeUrl } from "../../services/display";

type MarkdownNode = {
  type: string;
  value?: string;
  url?: string;
  children?: MarkdownNode[];
};
function citationPlugin(citations: Citation[]) {
  const ids = new Set(citations.map((citation) => citation.id));
  return () => (tree: MarkdownNode) => {
    const walk = (node: MarkdownNode) => {
      if (!node.children || ["link", "code", "inlineCode"].includes(node.type))
        return;
      const children: MarkdownNode[] = [];
      for (const child of node.children) {
        if (child.type === "text" && child.value) {
          const text = child.value;
          const pattern = /\[([^\]\n]+)\]/g;
          let last = 0;
          let match: RegExpExecArray | null;
          while ((match = pattern.exec(text))) {
            const citationId = match[1].replace(/^출처\s*:\s*/, "").trim();
            if (!ids.has(citationId)) continue;
            if (match.index > last)
              children.push({
                type: "text",
                value: text.slice(last, match.index),
              });
            children.push({
              type: "link",
              url: `citation:${encodeURIComponent(citationId)}`,
              children: [{ type: "text", value: citationId }],
            });
            last = match.index + match[0].length;
          }
          children.push({ type: "text", value: text.slice(last) });
        } else {
          walk(child);
          children.push(child);
        }
      }
      node.children = children;
    };
    walk(tree);
  };
}
export function SafeMarkdown({
  content,
  citations = [],
  onCitation,
}: {
  content: string;
  citations?: Citation[];
  onCitation?: (citation: Citation) => void;
}) {
  const plugin = useMemo(() => citationPlugin(citations), [citations]);
  const citationMap = useMemo(
    () =>
      new Map(
        citations.map((citation, index) => [
          citation.id,
          { citation, number: index + 1 },
        ]),
      ),
    [citations],
  );
  return (
    <div className="markdown">
      <ReactMarkdown
        skipHtml
        remarkPlugins={[remarkGfm, plugin]}
        urlTransform={(url) =>
          url.startsWith("citation:") ? url : safeUrl(url) || ""
        }
        components={{
          img: () => null,
          a: ({ href, children }) => {
            if (href?.startsWith("citation:")) {
              let citationId = "";
              try {
                citationId = decodeURIComponent(href.slice(9));
              } catch {
                /* Malformed untrusted links remain inert text. */
              }
              const entry = citationMap.get(citationId);
              const citation = entry?.citation;
              return citation && onCitation ? (
                <button
                  className="inline-citation"
                  onClick={() => onCitation(citation)}
                  title={citation.title}
                  aria-label={`출처 ${entry.number}: ${citation.title}`}
                >
                  {entry.number}
                </button>
              ) : (
                <span>{children}</span>
              );
            }
            const safe = safeUrl(href);
            return safe ? (
              <a href={safe} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            ) : (
              <span>{children}</span>
            );
          },
          table: ({ children }) => (
            <div className="table-scroll">
              <table>{children}</table>
            </div>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

/** Keep stored frontmatter visible without Markdown interpreting YAML as a large Setext heading. */
export function DocumentMarkdown({ content }: { content: string }) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(content);
  if (!match) return <SafeMarkdown content={content} />;
  return (
    <>
      <details className="document-frontmatter">
        <summary>파일에 기록된 메타데이터</summary>
        <p>원문 파일의 기록입니다. 공식성이나 정확성 검증을 뜻하지 않습니다.</p>
        <pre>{match[1]}</pre>
      </details>
      <SafeMarkdown content={content.slice(match[0].length)} />
    </>
  );
}
