// Shapes returned by UI/api/presenters.py. Display strings are pre-formatted by frostline.fmt on the server.

export type Tone = "good" | "neutral" | "warn" | "alert" | "muted";
export type Row = [string, string];
export interface Table { columns: string[]; rows: (string | number | boolean | null)[][] }
export interface Figure { data: unknown[]; layout: Record<string, unknown> }

export interface Fact { label: string; text: string; status: string }
export interface Location {
  id: string; name: string; short: string; role: string; road_id: string; road_name: string; road_kind: string; road_kind_label: string;
  lat: number | null; lon: number | null; mapped: boolean; region: string; sampling_point: string; setting: string; access: string; station: string;
  cell_elevation_m: number | null; facts: Fact[]; caution: string; is_primary_pair: boolean;
  cell: { center_lat: number; center_lon: number; south: number; north: number; west: number; east: number } | null;
  ranges?: { nasa: [number, number]; road: [number, number] }; variables?: string[];
}
export interface Variable {
  id: string; label: string; short: string; kind: "environmental" | "road"; tier: "core" | "exploratory"; unit: string; definition: string; why: string;
  source_id: string; power_parameter: string; temporal_resolution: string; spatial_resolution: string; valid_first: number; valid_last: number;
  locations: string; fixed_windows: [number, number][]; is_temperature: boolean; decimals: number; slope_decimals: number; phrase: string; unit_per_decade: string;
  limitations: string[]; quality: string;
}
export interface Question { id: string; text: string; blurb: string; variables: string[]; reasons: Record<string, string>; next_view: string; next_label: string }
export interface Source { id: string; name: string; kind: string; citation: string; url: string; resolution: string; note: string }

export interface Bootstrap {
  app: { name: string; team: string; tagline: string; version: string; method_id: string; code_version: string; digest: string };
  defaults: { location: string; variable: string };
  min_seasons: number;
  locations: Record<string, Location>;
  primary: string[];
  variables: Record<string, Variable>;
  questions: Record<string, Question>;
  sources: Record<string, Source>;
  state_labels: Record<string, string>;
  state_tone: Record<string, Tone>;
  road_note: string;
  bias_caveat: string;
  facts: Record<string, any>;
  giovanni: boolean;
  ranges: Record<string, Record<string, [number, number]>>;
}

export interface Finding {
  location_id: string; variable_id: string; first: number; last: number; n: number; n_expected: number; status: string; state: string; state_label: string;
  window_kind: string; estimated: boolean; tone: Tone; sentence: string; extra_sentences: string[]; q: number | null; cross_checked: boolean; stored_source: string | null;
  is_temperature: boolean; stat_rows?: Row[];
  display: { slope: string | null; unit: string; direction: string; interval: string | null; bb_interval: string | null; p: string | null; q: string | null;
             period: string; meta: string; title: string; provenance: string };
}

export interface Metric { kicker: string; value: string; unit: string; description: string; source: string }

export interface Observatory {
  hero_finding: Finding; hero_chart: Figure; hero_caption: string; metrics: Metric[]; release: string; intro_metrics: Metric[];
}

export interface Investigation {
  finding: Finding; plain: string; chart: Figure; fixed: boolean; status_meta: string; chart_caption: string; exploratory_caveat: boolean;
  season_table: Table; thaw_note?: string; why_rows: Row[]; method_rows: Row[];
  robustness: { kind: "table"; table: Table; caption: string } | { kind: "forest"; chart: Figure; caption: string } | { kind: "none"; caption: string };
  selection: { loc: string; var: string; first: number; last: number };
}

export interface Status { state: string; state_label: string; tone: Tone; n: number; fixed: boolean; meta: string; selection: { loc: string; var: string; first: number; last: number } }

export interface Recommendation { variable: string; kicker: string; label: string; fit: string; why: string; phrase: string; source: string; state: string; tone: Tone; state_label: string; range: [number, number] }
export interface QuestionView { id: string; text: string; blurb: string; next_view: string; next_label: string; recommendations: Recommendation[]; footnote: string; thaw_note: string | null }

export interface ComparePanel { label: string; tone: Tone; source: string; sentence: string; estimated: boolean; value: string; unit?: string; meta?: string }
export interface CompareView {
  variable: string; env_variables: string[]; first: number; last: number; period: string; substituted: boolean; substitute_note: string;
  chart: Figure; chart_caption: string; diff: ComparePanel; a: Finding; b: Finding; table: Table; table_caption: string;
  diff_chart: Figure; forest_chart: Figure; settings: { name: string; rows: Row[] }[]; is_temperature: boolean;
}

export interface CorridorOverview { kicker: string; name: string; setting: string; rows: Row[]; caution: string; road_note: string }
export interface CorridorRoad { measure: string; chart: Figure; full: Finding; nasa: Finding; note: string; table: Table }
export interface CorridorEnv { variable: string; chart: Figure; finding: Finding; thaw_note: string }
export interface CorridorTimeline { variable: string; years: number[]; year: number; winter: string; chart: Figure; record: Row[]; overlap: string | null; note: string }
export interface CorridorAssociations {
  table: Table; note: string; overlap: string | null;
  snow: { chart: Figure; value: string; unit: string; meta: string; text: string; source: string } | null;
}
export interface RoutesView { metric: string; window: string; chart: Figure; table: Table; note: string }
export interface Conclusion { label: string; paragraphs: string[]; source: string }
export interface DemoRoad { chart: Figure; finding: Finding; conclusion: string[] }

export interface Dimension { key: string; title: string; state: string; summary: string; reasons: string[]; sources: string[]; tone: Tone }
export interface Layer { key: string; title: string; question: string; items: string[] }
export interface Report { headline: string; suitability: string; dimensions: Dimension[]; layers: Layer[]; files: string[] }
export interface EvidenceView { lede: string; report: Report; state: string; state_label: string; tone: Tone }
export interface Disagreement {
  metrics: Metric[]; bias_chart: Figure; bias_caption: string; fdd_chart: Figure; fdd_caption: string; trend_table: Table; trend_note: string;
  aklavik_table: Table; aklavik_caption: string; meaning: string[];
}
export interface MultipleTesting { intro: string; metrics: Metric[]; chart: Figure; chart_caption: string; families: Table; all: Table; note: string }
export interface Methods {
  method_rows: Row[]; data_rows: Row[]; sources: Source[]; power_ack: string; literature: string[]; software: string[]; file_hashes: Table;
  giovanni: { trends: Table; check: Table } | null; giovanni_rows: Row[]; review_rows: Row[]; locations_table: Table; extend_rows: Row[]; version_line: string; catalogue: Table;
}
