import type { Draft, Route } from "../types/contracts";

const key = (userId: string, conversationId?: string) =>
  `knowledge-hub.draft.v1.${userId}.${conversationId || "new"}`;
export const workspaceStorage = {
  load(userId: string, conversationId?: string): Partial<Draft> | null {
    try {
      const raw = localStorage.getItem(key(userId, conversationId));
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },
  save(
    userId: string,
    conversationId: string | undefined,
    draft: Draft,
  ): boolean {
    try {
      localStorage.setItem(key(userId, conversationId), JSON.stringify(draft));
      return true;
    } catch {
      return false;
    }
  },
  removeNew(userId: string) {
    try {
      localStorage.removeItem(key(userId));
    } catch {
      /* A denied storage area must not prevent conversation use. */
    }
  },
};
export function readRoute(): Route {
  const [screen, id] = window.location.hash.replace(/^#\/?/, "").split("/");
  let decoded: string | undefined;
  try {
    decoded = id ? decodeURIComponent(id) : undefined;
  } catch {
    decoded = undefined;
  }
  if (screen === "research") return { screen: "research", id: decoded };
  if (screen === "personal-wiki")
    return { screen: "personal-wiki", id: decoded };
  if (screen === "review") return { screen: "review" };
  return { screen: "conversation", id: decoded };
}
export function writeRoute(route: Route, replace = false) {
  const hash = `#/${route.screen}${route.id ? `/${encodeURIComponent(route.id)}` : ""}`;
  if (replace) window.history.replaceState(null, "", hash);
  else window.history.pushState(null, "", hash);
}
