// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { replyFollowScrollTop } from "./replyScroll";

afterEach(() => {
  document.body.innerHTML = "";
  vi.restoreAllMocks();
});
function viewport(markup: string) {
  const element = document.createElement("div");
  element.innerHTML = markup;
  document.body.appendChild(element);
  Object.defineProperties(element, {
    scrollHeight: { value: 4000 },
    clientHeight: { value: 600 },
  });
  vi.spyOn(element, "getBoundingClientRect").mockReturnValue(
    new DOMRect(0, 100, 800, 600),
  );
  return element;
}
describe("following real answer text", () => {
  it("keeps the first generated paragraph visible even when many source cards already extend the message", () => {
    const element = viewport(
      '<article id="message-m1"><div class="answer-body"><section class="answer-section"><div class="markdown">실제 도착한 첫 문장</div></section><section class="answer-section"><div class="citation-list">긴 출처 카드 목록</div></section></div></article>',
    );
    const text = element.querySelector<HTMLElement>(".markdown")!;
    vi.spyOn(text, "getBoundingClientRect").mockReturnValue(
      new DOMRect(0, 300, 800, 100),
    );
    const position = replyFollowScrollTop(element, "m1");
    expect(position).toBe(0);
    expect(position).not.toBe(element.scrollHeight - element.clientHeight);
  });
  it("follows the newest generated section without following supplementary cards below it", () => {
    const element = viewport(
      '<article id="message-m1"><div class="answer-body"><section class="answer-section"><div class="markdown">먼저 도착한 설명</div></section><section class="answer-section"><div class="markdown">지금 작성되는 조건</div><div class="source-views">출처별 관점</div></section><section class="answer-section"><div class="citation-list">출처</div></section></div></article>',
    );
    const paragraphs = element.querySelectorAll<HTMLElement>(".markdown");
    vi.spyOn(paragraphs[0], "getBoundingClientRect").mockReturnValue(
      new DOMRect(0, 300, 800, 100),
    );
    vi.spyOn(paragraphs[1], "getBoundingClientRect").mockReturnValue(
      new DOMRect(0, 800, 800, 250),
    );
    const position = replyFollowScrollTop(element, "m1");
    expect(position).toBeGreaterThan(0);
    expect(1050 - 100 - position).toBeLessThanOrEqual(element.clientHeight);
    expect(position).toBeLessThan(1000);
  });
});
