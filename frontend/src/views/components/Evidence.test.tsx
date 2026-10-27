// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { CitationList, RelationCards, SourceViewCards } from "./Evidence";
import { SafeMarkdown } from "./SafeMarkdown";
import { ontologyRepository } from "../../repositories/api";
import type { Citation, Relation, SourceView } from "../../types/contracts";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
const citation: Citation = {
  id: "C1",
  sourceRevisionId: "r1",
  passageId: "p1",
  title: "Fixture source · test only",
  locator: "접합 조건",
  excerpt: "원문 조건",
  publisher: "테스트 발행처",
};
const relation: Relation = {
  id: "rel1",
  fromConceptId: "c1",
  toConceptId: "c2",
  fromName: "접합",
  toName: "적층",
  type: "precedes",
  summary: "조건이 확인된 연결",
  conditions: "동일한 대상 공정에 한함",
  status: "supported",
  evidence: [citation],
};

describe("relation exploration boundaries", () => {
  it("groups passages by revision while preserving inline citation numbers and earlier-answer provenance", () => {
    const onOpen = vi.fn();
    const other = { ...citation, id: "C2", passageId: "p2", sourceRevisionId: "r2", title: "다른 판본" };
    const previous = { ...citation, id: "C3", passageId: "p3", locator: "결과", sourceType: "editorial_summary", contextOrigin: "earlier_answer" };
    render(<CitationList citations={[citation, other, previous]} onOpen={onOpen} />);
    expect(screen.getByText("자료 판본 2개 · 근거 구간 3개")).toBeTruthy();
    const group = screen.getByText("Fixture source · test only").closest("details")!;
    expect(group.textContent).toContain("2개 구간");
    expect(group.open).toBe(false);
    fireEvent.click(screen.getByText("Fixture source · test only"));
    const passage = screen.getByRole("button", { name: /출처 3:.*결과/ });
    expect(passage.textContent).toContain("이전 답변의 출처");
    fireEvent.click(passage);
    expect(onOpen).toHaveBeenCalledWith(previous);
    const otherGroup = screen.getByText("다른 판본").closest("details")!;
    expect(otherGroup.open).toBe(false);
    fireEvent.click(screen.getByText("다른 판본"));
    expect(screen.getByRole("button", { name: /출처 2:.*다른 판본/ })).toBeTruthy();
  });
  it.each([
    ["is_a", "상위 개념"],
    ["alternative_to", "대체 개념"],
  ])(
    "labels the canonical %s relation without reversing its target",
    (type, label) => {
      render(
        <RelationCards
          relations={[{ ...relation, type }]}
          onOpen={vi.fn()}
          onFollowup={vi.fn()}
        />,
      );
      const trigger = screen.getByRole("button", { name: new RegExp(label) });
      expect(trigger.textContent).toContain(relation.fromName);
      expect(trigger.textContent).toContain(relation.toName);
      expect(trigger.textContent).not.toContain(type);
    },
  );
  it("primary expansion is local; source reading and explicit followup are separate actions", () => {
    const onOpen = vi.fn();
    const onFollowup = vi.fn();
    render(
      <RelationCards
        relations={[relation]}
        onOpen={onOpen}
        onFollowup={onFollowup}
      />,
    );
    const trigger = screen.getByRole("button", { name: /후속 절차/ });
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(trigger);
    expect(trigger.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText("동일한 대상 공정에 한함")).toBeTruthy();
    expect(onOpen).not.toHaveBeenCalled();
    expect(onFollowup).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Fixture source · test only"));
    fireEvent.click(screen.getByRole("button", { name: /Fixture source/ }));
    expect(onOpen).toHaveBeenCalledWith(citation);
    expect(onFollowup).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole("button", { name: "이 개념으로 이어서 질문" }),
    );
    expect(onFollowup).toHaveBeenCalledWith(relation);
  });
  it("keeps an actual citation locator and does not require a brittle quote match to expose source reading", () => {
    const onOpen = vi.fn();
    render(
      <CitationList
        citations={[
          { ...citation, excerpt: "발췌의 줄바꿈이 달라도 원문 열기는 제공" },
        ]}
        onOpen={onOpen}
      />,
    );
    const group = screen.getByText("Fixture source · test only").closest("details")!;
    expect(group.open).toBe(false);
    fireEvent.click(screen.getByText("Fixture source · test only"));
    expect(group.open).toBe(true);
    fireEvent.click(screen.getByRole("button"));
    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/접합 조건/)).toBeTruthy();
  });
});
describe("source viewpoint filters", () => {
  it("filters display without generation and performs only a read on explicit registered-view lookup", async () => {
    const first: SourceView = {
      id: "v1",
      conceptId: "c1",
      sourceRevisionId: "r1",
      publisherId: "p1",
      publisher: "발행처 A",
      author: "외부 저자",
      attributedTo: "외부 저자",
      attributionBasis: "author_byline",
      sourceType: "column",
      aspect: "조건",
      summary: "첫 관점",
      status: "supported",
      evidence: [citation],
    };
    const second: SourceView = {
      ...first,
      id: "v2",
      publisherId: "p2",
      publisher: "발행처 B",
      attributedTo: "연구 저자",
      summary: "둘째 관점",
    };
    const read = vi
      .spyOn(ontologyRepository, "sourceViews")
      .mockResolvedValue({ items: [first] });
    const compare = vi.fn();
    const { container } = render(
      <SourceViewCards
        views={[first, second]}
        onOpen={vi.fn()}
        onCompare={compare}
      />,
    );
    const section = container.querySelector<HTMLDetailsElement>("details.source-views");
    expect(section?.open).toBe(false);
    fireEvent.click(screen.getByText("자료에서 정리한 관점"));
    expect(section?.open).toBe(true);
    expect(screen.getByText(/출처와 항목을 기준으로 비교 질문 초안을 준비합니다/)).toBeTruthy();
    fireEvent.change(screen.getByRole("combobox", { name: "발행처 필터" }), {
      target: { value: "p1" },
    });
    expect(screen.getByText("첫 관점")).toBeTruthy();
    expect(screen.queryByText("둘째 관점")).toBeNull();
    expect(read).not.toHaveBeenCalled();
    expect(compare).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "등록 관점 조회" }));
    await waitFor(() =>
      expect(read).toHaveBeenCalledWith("c1", {
        publisherId: "p1",
        sourceType: "",
        aspect: "",
      }),
    );
    expect(compare).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("checkbox", { name: "외부 저자" }));
    fireEvent.click(
      screen.getByRole("button", { name: "선택 관점으로 질문 준비" }),
    );
    expect(compare).toHaveBeenCalledWith([first]);
  });
});
describe("untrusted markdown", () => {
  it("recognizes the provider's [출처: id] contract only for known IDs and leaves code untouched", () => {
    const onOpen = vi.fn();
    const { container } = render(
      <SafeMarkdown
        content={
          "두 표기 [C1] · [출처: C1] · 미확인 [출처: missing]\n\n`[출처: C1]`\n\n```text\n[출처: C1]\n```"
        }
        citations={[citation]}
        onCitation={onOpen}
      />,
    );
    const buttons = screen.getAllByRole("button", {
      name: "출처 1: Fixture source · test only",
    });
    expect(buttons).toHaveLength(2);
    expect(buttons[0].textContent).toBe("1");
    fireEvent.click(buttons[1]);
    expect(onOpen).toHaveBeenCalledWith(citation);
    expect(container.textContent).toContain("[출처: missing]");
    expect(container.querySelectorAll("code button")).toHaveLength(0);
    expect(container.querySelectorAll("code")).toHaveLength(2);
  });
  it("opens only known evidence, disables remote images/raw HTML and keeps external links safe", () => {
    const onOpen = vi.fn();
    const { container } = render(
      <SafeMarkdown
        content={
          "근거 [C1] · 미확인 [invented]\n\n[외부](https://example.com)\n\n![tracking](https://example.com/pixel.png)\n\n<script>alert(1)</script>"
        }
        citations={[citation]}
        onCitation={onOpen}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: "출처 1: Fixture source · test only",
      }),
    );
    expect(onOpen).toHaveBeenCalledWith(citation);
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("script")).toBeNull();
    expect(screen.getByRole("link", { name: "외부" }).getAttribute("rel")).toBe(
      "noopener noreferrer",
    );
    expect(screen.queryByRole("button", { name: "invented" })).toBeNull();
  });
});
