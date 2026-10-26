import {
  conversationRepository,
  researchRepository,
} from "../repositories/api";
import { safeUrl } from "./display";
import type { ResearchCard } from "../types/contracts";

export const researchService = {
  search(query: string, conversationId?: string) {
    if (!query.trim())
      throw new Error("찾고 싶은 문헌의 질문이나 검색어를 입력해 주세요.");
    return researchRepository.search(query.trim(), conversationId);
  },
  fetch(card: ResearchCard, query: string, conversationId?: string) {
    const url = safeUrl(card.url);
    if (!url) throw new Error("이 문헌에 열 수 있는 원문 주소가 없습니다.");
    return researchRepository.fetch(url, query.trim(), conversationId);
  },
  async transfer(
    cards: ResearchCard[],
    query: string,
    conditions: string,
    conversationId?: string,
  ) {
    if (!cards.length) throw new Error("가져올 문헌을 선택해 주세요.");
    if (!cards.some((card) => card.content?.trim()))
      throw new Error(
        "선택한 문헌의 본문이나 초록을 먼저 확인해 주세요. 서지정보만으로는 답변 근거에 첨부할 수 없습니다.",
      );
    const id =
      conversationId ||
      (
        await conversationRepository.create(
          query.trim().slice(0, 80) || "문헌으로 시작한 대화",
        )
      ).id;
    const result = await researchRepository.transfer(
      id,
      [...new Set(cards.map((card) => card.id))],
      query.trim(),
      conditions.trim(),
    );
    return { ...result, conversationId: id };
  },
};
