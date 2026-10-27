import { describe, expect, it } from "vitest";
import { citationIdsFromLabel } from "./citationService";

describe("citation labels", () => {
  it("splits provider and bare labels consistently while preserving opaque IDs", () => {
    expect(citationIdsFromLabel(" 출처: psg_A, psg_B; psg_C, psg_A ")).toEqual(["psg_A", "psg_B", "psg_C"]);
    expect(citationIdsFromLabel(" C1 ; C2, , ")).toEqual(["C1", "C2"]);
  });
});
