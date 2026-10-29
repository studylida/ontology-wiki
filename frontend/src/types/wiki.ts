export type WikiAuthor = {id: string; username: string};
export type WikiRevisionSummary = {
  id: string; pageId: string; number: number; title: string; changeSummary: string;
  editor: WikiAuthor; createdAt: string; restoredFromId: string | null;
};
export type WikiRevision = WikiRevisionSummary & {markdown: string; sourceNote: string; aliases?: string[]; meaning?: string};
export type WikiPage = {
  id: string; title: string; currentRevisionId: string; revisionNumber: number; version: number;
  locked: boolean; canEdit: boolean; canProtect: boolean; creator: WikiAuthor; editor: WikiAuthor;
  createdAt: string; updatedAt: string; aliases?: string[]; meaning?: string;
};
export type WikiDetail = WikiPage & {revision: WikiRevision};
export type WikiList<T> = {items: T[]; total: number; offset: number; limit: number};
export type WikiDraft = {title: string; markdown: string; sourceNote: string; changeSummary: string; aliasesText?: string; meaning?: string};
export type WikiWrite = Omit<WikiDraft, 'aliasesText'> & {aliases?: string[]};
export type WikiComparison = {before: WikiRevision; after: WikiRevision; diff: string};
export type WikiMutation = {pageId: string; revisionId: string; version: number; replayed: boolean};
export type WikiCommand =
  | {kind: 'create'; body: WikiWrite & {requestId: string}}
  | {kind: 'edit'; pageId: string; body: WikiWrite & {requestId: string; baseVersion: number}}
  | {kind: 'restore'; pageId: string; body: {requestId: string; baseVersion: number; revisionId: string}}
  | {kind: 'protect'; pageId: string; body: {requestId: string; baseVersion: number; locked: boolean}};

/** Only a submitted command is retained for recovery; this is not an autosaved draft. */
export type WikiPending = {command: WikiCommand; receipt: WikiMutation | null};
const record = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const text = (value: unknown, max: number) => typeof value === 'string' && value.length <= max && !value.includes('\0');
const id = (value: unknown) => text(value, 128) && (value as string).length > 0;
const version = (value: unknown) => typeof value === 'number' && Number.isSafeInteger(value) && value > 0;
export function isWikiPending(value: unknown): value is WikiPending {
  if (!record(value) || !record(value.command) || !record(value.command.body)) return false;
  const c = value.command, b = value.command.body;
  if (typeof b.requestId !== 'string' || !/^[A-Za-z0-9_.:-]{8,128}$/.test(b.requestId)) return false;
  if (c.kind !== 'create' && (!id(c.pageId) || !version(b.baseVersion))) return false;
  if (c.kind === 'create' || c.kind === 'edit') {
    if ((b.aliases !== undefined && (!Array.isArray(b.aliases) || b.aliases.length > 30 || !b.aliases.every(x => text(x, 300)))) ||
        (b.meaning !== undefined && !text(b.meaning, 500))) return false;
    if (!text(b.title, 300) || !text(b.markdown, 100000) || !text(b.sourceNote, 10000) || !text(b.changeSummary, 500)) return false;
  } else if (c.kind === 'restore') { if (!id(b.revisionId)) return false; }
  else if (c.kind === 'protect') { if (typeof b.locked !== 'boolean') return false; }
  else return false;
  const receipt = value.receipt;
  return receipt === null || (record(receipt) && id(receipt.pageId) && id(receipt.revisionId) &&
    version(receipt.version) && typeof receipt.replayed === 'boolean' && (c.kind === 'create' || receipt.pageId === c.pageId));
}
