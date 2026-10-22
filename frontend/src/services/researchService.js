/** Which selected records actually contain acquired evidence, rather than only a title. */
export function usableEvidenceIds(feed, selectedIds) {
  return feed.filter((item) => selectedIds.includes(item.id) && item.quote?.trim()
    && ['registered_excerpt', 'source_excerpt', 'abstract'].includes(item.retrievalStatus)).map((item) => item.id);
}
