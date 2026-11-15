import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router";
import { useBootstrap, type Sel } from "./api";
import type { Bootstrap } from "./types";

/*
 * The shared investigation (location, variable, analysis window, guiding question).
 * It lives in the URL (?loc=&var=&from=&to=&q=) so every view reads the same selection, a link reproduces it,
 * and the back button undoes a change. Rules mirror frostline/ui.py init_state and set_investigation:
 *  - a location must be one of the two documented case studies; a variable must be available there;
 *  - a new location or variable resets the window to that record's full range;
 *  - a window is clamped to the available range.
 */

export interface Change { loc?: string; variable?: string; window?: [number, number]; question?: string | null }

interface Ctx {
  boot: Bootstrap;
  sel: Sel;
  question: string | null;
  range: [number, number];
  showExploratory: boolean;
  setShowExploratory: (v: boolean) => void;
  set: (c: Change, opts?: { replace?: boolean }) => void;
  go: (path: string, c?: Change) => void;
  searchFor: (c?: Change) => string;
}

const InvestigationContext = createContext<Ctx | null>(null);

function resolve(boot: Bootstrap, params: URLSearchParams): { sel: Sel; question: string | null } {
  const loc = boot.primary.includes(params.get("loc") ?? "") ? params.get("loc")! : boot.defaults.location;
  const avail = boot.ranges[loc];
  const v = params.get("var") ?? "";
  const variable = v in avail ? v : boot.defaults.variable;
  const [lo, hi] = avail[variable];
  let first = Number(params.get("from"));
  let last = Number(params.get("to"));
  if (!(Number.isInteger(first) && Number.isInteger(last) && lo <= first && first <= last && last <= hi)) {
    first = lo;
    last = hi;
  }
  const q = params.get("q");
  return { sel: { loc, var: variable, first, last }, question: q && q in boot.questions ? q : null };
}

function apply(boot: Bootstrap, cur: { sel: Sel; question: string | null }, c: Change): { sel: Sel; question: string | null } {
  let { loc, var: variable, first, last } = cur.sel;
  if (c.loc && boot.primary.includes(c.loc)) loc = c.loc;
  if (c.variable) variable = c.variable;
  if (!(variable in boot.ranges[loc])) variable = boot.defaults.variable;
  const [lo, hi] = boot.ranges[loc][variable];
  if (c.window) {
    first = Math.max(lo, Math.min(c.window[0], c.window[1]));
    last = Math.min(hi, Math.max(c.window[0], c.window[1]));
  } else if (c.loc || c.variable) {
    first = lo;
    last = hi;
  }
  first = Math.max(lo, Math.min(first, hi));
  last = Math.max(first, Math.min(last, hi));
  const question = c.question !== undefined ? c.question : cur.question;
  return { sel: { loc, var: variable, first, last }, question };
}

function toSearch(boot: Bootstrap, s: { sel: Sel; question: string | null }, keep?: URLSearchParams) {
  const p = new URLSearchParams();
  if (keep) for (const [k, v] of keep) if (!["loc", "var", "from", "to", "q"].includes(k)) p.set(k, v);
  const [lo, hi] = boot.ranges[s.sel.loc][s.sel.var];
  p.set("loc", s.sel.loc);
  p.set("var", s.sel.var);
  if (s.sel.first !== lo || s.sel.last !== hi) {
    p.set("from", String(s.sel.first));
    p.set("to", String(s.sel.last));
  }
  if (s.question) p.set("q", s.question);
  return `?${p.toString()}`;
}

export function InvestigationProvider({ boot, children }: { boot: Bootstrap; children: ReactNode }) {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [showExploratory, setShowExploratoryState] = useState(() => {
    try { return sessionStorage.getItem("fl_exploratory") === "1"; } catch { return false; }
  });
  const setShowExploratory = useCallback((v: boolean) => {
    setShowExploratoryState(v);
    try { sessionStorage.setItem("fl_exploratory", v ? "1" : "0"); } catch { /* storage unavailable */ }
  }, []);

  const cur = useMemo(() => resolve(boot, params), [boot, params]);

  const searchFor = useCallback((c?: Change) => toSearch(boot, c ? apply(boot, cur, c) : cur), [boot, cur]);

  const set = useCallback((c: Change, opts?: { replace?: boolean }) => {
    const next = apply(boot, cur, c);
    navigate({ pathname: location.pathname, search: toSearch(boot, next, params) }, { replace: opts?.replace ?? false, preventScrollReset: true });
  }, [boot, cur, navigate, location.pathname, params]);

  const go = useCallback((path: string, c?: Change) => {
    navigate({ pathname: path, search: toSearch(boot, c ? apply(boot, cur, c) : cur) });
  }, [boot, cur, navigate]);

  const variable = boot.variables[cur.sel.var];
  const effectiveExploratory = showExploratory || variable.tier === "exploratory";

  const value = useMemo<Ctx>(() => ({
    boot, sel: cur.sel, question: cur.question, range: boot.ranges[cur.sel.loc][cur.sel.var],
    showExploratory: effectiveExploratory, setShowExploratory, set, go, searchFor,
  }), [boot, cur, effectiveExploratory, setShowExploratory, set, go, searchFor]);

  return <InvestigationContext.Provider value={value}>{children}</InvestigationContext.Provider>;
}

export function useInv() {
  const c = useContext(InvestigationContext);
  if (!c) throw new Error("useInv outside InvestigationProvider");
  return c;
}

export function useBoot() {
  const { data } = useBootstrap();
  return data!;
}

export const winter = (y: number) => `${y}/${String((y + 1) % 100).padStart(2, "0")}`;
export const period = (a: number, b: number) => `${winter(a)} to ${winter(b)}`;
