import { useCallback, useEffect, useState } from "react";
import { readRoute, writeRoute } from "../repositories/workspaceStorage";
import type { Route } from "../types/contracts";
export function useRoute() {
  const [route, setRoute] = useState<Route>(readRoute);
  useEffect(() => {
    const restore = () => setRoute(readRoute());
    window.addEventListener("popstate", restore);
    window.addEventListener("hashchange", restore);
    return () => {
      window.removeEventListener("popstate", restore);
      window.removeEventListener("hashchange", restore);
    };
  }, []);
  const navigate = useCallback((next: Route, replace = false) => {
    writeRoute(next, replace);
    setRoute(next);
  }, []);
  return { route, navigate };
}
