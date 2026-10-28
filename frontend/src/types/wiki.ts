export type WikiAuthor = {id: string; username: string};
export type WikiRevisionSummary = {
  id: string; pageId: string; number: number; title: string; changeSummary: string;
  editor: WikiAuthor; createdAt: string; restoredFromId: string | null;
};
export type WikiRevision = WikiRevisionSummary & {markdown: string; sourceNote: string};
export type WikiPage = {
  id: string; title: string; currentRevisionId: string; revisionNumber: number; version: number;
  locked: boolean; canEdit: boolean; canProtect: boolean; creator: WikiAuthor; editor: WikiAuthor;
  createdAt: string; updatedAt: string;
};
export type WikiDetail = WikiPage & {revision: WikiRevision};
export type WikiList<T> = {items: T[]; total: number; offset: number; limit: number};
export type WikiDraft = {title: string; markdown: string; sourceNote: string; changeSummary: string};
export type WikiComparison = {before: WikiRevision; after: WikiRevision; diff: string};
export type WikiMutation = {pageId: string; revisionId: string; version: number; replayed: boolean};
export type WikiCommand =
  | {kind: 'create'; body: WikiDraft & {requestId: string}}
  | {kind: 'edit'; pageId: string; body: WikiDraft & {requestId: string; baseVersion: number}}
  | {kind: 'restore'; pageId: string; body: {requestId: string; baseVersion: number; revisionId: string}}
  | {kind: 'protect'; pageId: string; body: {requestId: string; baseVersion: number; locked: boolean}};
