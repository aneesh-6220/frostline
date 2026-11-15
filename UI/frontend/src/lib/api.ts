import { keepPreviousData, useQuery } from "@tanstack/react-query";
import type * as T from "./types";

export class ApiError extends Error {
  status: number;
  filename?: string;
  constructor(message: string, status: number, filename?: string) {
    super(message);
    this.status = status;
    this.filename = filename;
  }
}

function qs(params: Record<string, string | number | boolean | null | undefined>) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") p.set(k, String(v));
  const s = p.toString();
  return s ? `?${s}` : "";
}

export function apiUrl(path: string, params: Record<string, string | number | boolean | null | undefined> = {}) {
  return `/api${path}${qs(params)}`;
}

async function get<R>(path: string, params: Record<string, string | number | boolean | null | undefined> = {}): Promise<R> {
  const res = await fetch(apiUrl(path, params), { headers: { Accept: "application/json" } });
  if (!res.ok) {
    let body: any = null;
    try { body = await res.json(); } catch { /* not json */ }
    const msg = body?.message || (typeof body?.detail === "string" ? body.detail : null) || `Request failed (${res.status})`;
    throw new ApiError(msg, res.status, body?.filename);
  }
  return res.json() as Promise<R>;
}

export async function getText(path: string, params: Record<string, string | number | boolean | null | undefined> = {}) {
  const res = await fetch(apiUrl(path, params));
  if (!res.ok) throw new ApiError(`Request failed (${res.status})`, res.status);
  return res.text();
}

const STATIC = { staleTime: Infinity, gcTime: Infinity } as const;
const LIVE = { staleTime: 5 * 60_000, placeholderData: keepPreviousData } as const;

export const useBootstrap = () => useQuery({ queryKey: ["bootstrap"], queryFn: () => get<T.Bootstrap>("/bootstrap"), ...STATIC });
export const useObservatory = () => useQuery({ queryKey: ["observatory"], queryFn: () => get<T.Observatory>("/observatory"), ...STATIC });

export interface Sel { loc: string; var: string; first: number; last: number }

export const useInvestigation = (s: Sel, height = 430, enabled = true) =>
  useQuery({ queryKey: ["investigation", s, height], queryFn: () => get<T.Investigation>("/investigation", { ...s, height }), enabled, ...LIVE });
export const useStatus = (s: Sel) => useQuery({ queryKey: ["status", s], queryFn: () => get<T.Status>("/status", { ...s }), ...LIVE });
export const useQuestion = (qid: string, loc: string) =>
  useQuery({ queryKey: ["question", qid, loc], queryFn: () => get<T.QuestionView>(`/questions/${qid}`, { loc }), ...LIVE });
export const useCompare = (v: string, first: number, last: number) =>
  useQuery({ queryKey: ["compare", v, first, last], queryFn: () => get<T.CompareView>("/compare", { var: v, first, last }), ...LIVE });
export const useCorridor = (loc: string) => useQuery({ queryKey: ["corridor", loc], queryFn: () => get<T.CorridorOverview>(`/corridor/${loc}`), ...STATIC });
export const useCorridorRoad = (loc: string, measure: string) =>
  useQuery({ queryKey: ["corridor-road", loc, measure], queryFn: () => get<T.CorridorRoad>(`/corridor/${loc}/road`, { measure }), ...LIVE });
export const useCorridorEnv = (loc: string, v: string) =>
  useQuery({ queryKey: ["corridor-env", loc, v], queryFn: () => get<T.CorridorEnv>(`/corridor/${loc}/environment`, { var: v }), ...LIVE });
export const useTimeline = (loc: string, v: string, year: number | null, height = 560) =>
  useQuery({ queryKey: ["timeline", loc, v, year, height], queryFn: () => get<T.CorridorTimeline>(`/corridor/${loc}/timeline`, { var: v, year, height }), ...LIVE });
export const useAssociations = (loc: string) =>
  useQuery({ queryKey: ["assoc", loc], queryFn: () => get<T.CorridorAssociations>(`/corridor/${loc}/associations`), ...STATIC });
export const useRoutes = (metric: string, window: string) =>
  useQuery({ queryKey: ["routes", metric, window], queryFn: () => get<T.RoutesView>("/routes", { metric, window }), ...LIVE });
export const useConclusion = (loc: string) =>
  useQuery({ queryKey: ["conclusion", loc], queryFn: () => get<T.Conclusion>(`/corridor/${loc}/conclusion`), ...STATIC });
export const useDemoRoad = (loc: string) => useQuery({ queryKey: ["demo-road", loc], queryFn: () => get<T.DemoRoad>(`/demo/road/${loc}`), ...LIVE });
export const useEvidence = (s: Sel) => useQuery({ queryKey: ["evidence", s], queryFn: () => get<T.EvidenceView>("/evidence", { ...s }), ...LIVE });
export const useDisagreement = () => useQuery({ queryKey: ["disagreement"], queryFn: () => get<T.Disagreement>("/evidence/disagreement"), ...STATIC });
export const useMultipleTesting = () => useQuery({ queryKey: ["mt"], queryFn: () => get<T.MultipleTesting>("/evidence/multiple-testing"), ...STATIC });
export const useMethods = () => useQuery({ queryKey: ["methods"], queryFn: () => get<T.Methods>("/methods"), ...STATIC });
export const useBriefHtml = (s: Sel, question: string | null) =>
  useQuery({ queryKey: ["brief", s, question], queryFn: () => getText("/brief", { ...s, question, format: "html" }), ...LIVE });
