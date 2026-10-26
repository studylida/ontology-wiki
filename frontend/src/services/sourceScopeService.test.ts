import { describe, expect, it } from "vitest";
import { publisherOptions, setPublisherGroup } from "./sourceScopeService";
import type { DocumentSummary } from "../types/contracts";

const document = (extra: Partial<DocumentSummary>): DocumentSummary => ({
  id: "d",
  title: "Fixture source",
  currentRevisionId: "r",
  reviewStatus: "approved",
  indexStatus: "pending",
  visibility: "shared_candidate",
  ...extra,
});
describe("publisher scope from actual document metadata", () => {
  it("deduplicates actual identifiers, excludes private sources and never derives company identity from a title", () => {
    const options = publisherOptions([
      document({
        id: "a",
        publisherId: "actual-publisher",
        publisher: "발행처",
        sourceType: "column",
      }),
      document({
        id: "b",
        publisherId: "actual-publisher",
        publisher: "발행처",
        sourceType: "paper",
      }),
      document({
        id: "c",
        title: "삼성이라는 단어만 들어 있는 제목",
        publisher: "이름만 있음",
      }),
      document({
        id: "d",
        publisherId: "private-publisher",
        visibility: "private",
      }),
    ]);
    expect(options).toEqual([
      {
        id: "actual-publisher",
        name: "발행처",
        approvedCount: 2,
        types: ["column", "paper"],
      },
    ]);
  });
  it("selects two independent publisher groups and changes only one group's AND predicate", () => {
    let groups = setPublisherGroup([], "p1", true);
    groups = setPublisherGroup(groups, "p2", true);
    groups = setPublisherGroup(groups, "p1", true, "paper");
    expect(groups).toEqual([
      { groupId: "publisher:p2", publisherId: "p2" },
      { groupId: "publisher:p1", publisherId: "p1", sourceType: "paper" },
    ]);
    expect(setPublisherGroup(groups, "p1", false)).toEqual([
      { groupId: "publisher:p2", publisherId: "p2" },
    ]);
  });
});
