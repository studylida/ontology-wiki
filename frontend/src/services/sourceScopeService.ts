import type { DocumentSummary, SourceGroup } from "../types/contracts";

export interface PublisherOption {
  id: string;
  name: string;
  approvedCount: number;
  types: string[];
}
export function publisherOptions(
  documents: DocumentSummary[],
): PublisherOption[] {
  const options = new Map<string, PublisherOption>();
  for (const document of documents) {
    if (!document.publisherId || document.visibility === "private") continue;
    const option = options.get(document.publisherId) || {
      id: document.publisherId,
      name: document.publisher || document.publisherId,
      approvedCount: 0,
      types: [],
    };
    if (document.reviewStatus === "approved") option.approvedCount++;
    if (document.sourceType && !option.types.includes(document.sourceType))
      option.types.push(document.sourceType);
    options.set(document.publisherId, option);
  }
  return [...options.values()].sort((a, b) =>
    a.name.localeCompare(b.name, "ko"),
  );
}
export function setPublisherGroup(
  groups: SourceGroup[],
  publisherId: string,
  enabled: boolean,
  sourceType = "",
): SourceGroup[] {
  const rest = groups.filter((group) => group.publisherId !== publisherId);
  return enabled
    ? [
        ...rest,
        {
          groupId: `publisher:${publisherId}`,
          publisherId,
          ...(sourceType ? { sourceType } : {}),
        },
      ]
    : rest;
}
