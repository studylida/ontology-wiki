export function citationIdsFromLabel(label: string): string[] {
  return [...new Set(label.trim().replace(/^출처\s*:\s*/, "").split(/[,;]/)
    .map((id) => id.trim()).filter(Boolean))];
}
