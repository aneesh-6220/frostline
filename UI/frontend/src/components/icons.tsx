import type { SVGProps } from "react";

/*
 * Frostline icon set. One family: 20px grid, 1.5px stroke, round caps and joins, no fills.
 * Drawn for this product (the hexagon-and-line motif comes from the Frostline mark), used only where an icon
 * genuinely helps: navigation, actions and callouts.
 */
type P = SVGProps<SVGSVGElement> & { size?: number };

function Base({ size = 18, children, ...rest }: P & { children: React.ReactNode }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round"
      strokeLinejoin="round" aria-hidden="true" focusable="false" {...rest}>
      {children}
    </svg>
  );
}

export const Icon = {
  Overview: (p: P) => <Base {...p}><path d="M10 2.8 16.3 6.4v7.2L10 17.2l-6.3-3.6V6.4z" /><path d="M2 10h16" /></Base>,
  Play: (p: P) => <Base {...p}><circle cx="10" cy="10" r="7.2" /><path d="m8.4 7.2 4.2 2.8-4.2 2.8z" /></Base>,
  Atlas: (p: P) => <Base {...p}><path d="M2.8 5.2 7.3 3.4l5.4 1.8 4.5-1.8v11.4l-4.5 1.8-5.4-1.8-4.5 1.8z" /><path d="M7.3 3.4v11.4M12.7 5.2v11.4" /></Base>,
  Question: (p: P) => <Base {...p}><path d="M3.5 4.6A1.6 1.6 0 0 1 5.1 3h9.8a1.6 1.6 0 0 1 1.6 1.6v7.6a1.6 1.6 0 0 1-1.6 1.6H9l-3.7 3v-3h-.2a1.6 1.6 0 0 1-1.6-1.6z" /><path d="M8.3 7.1a1.8 1.8 0 1 1 2.6 1.6c-.6.3-.9.7-.9 1.3M10 11.6v.1" /></Base>,
  Trend: (p: P) => <Base {...p}><path d="M3 16.5h14" /><path d="m3.5 12.6 3.6-3.4 3 2.4 5.9-6" /><path d="M13.2 5.6H16v2.8" /></Base>,
  Compare: (p: P) => <Base {...p}><path d="M6 3.5v13M14 3.5v13" /><path d="M3 8.5h6M11 11.5h6" /><circle cx="6" cy="8.5" r="0.6" /><circle cx="14" cy="11.5" r="0.6" /></Base>,
  Route: (p: P) => <Base {...p}><circle cx="5" cy="15" r="2" /><circle cx="15" cy="5" r="2" /><path d="M7 15h5.5a2.5 2.5 0 0 0 0-5h-5a2.5 2.5 0 0 1 0-5H13" /></Base>,
  Evidence: (p: P) => <Base {...p}><path d="M10 2.6 16 5v4.6c0 3.6-2.5 6.3-6 7.8-3.5-1.5-6-4.2-6-7.8V5z" /><path d="m7.4 9.9 1.8 1.8 3.5-3.6" /></Base>,
  Brief: (p: P) => <Base {...p}><path d="M5 2.8h6.6L15 6.2v10.1a.9.9 0 0 1-.9.9H5.9a.9.9 0 0 1-.9-.9z" /><path d="M11.4 2.8v3.6H15M7.5 10h5M7.5 13h3.5" /></Base>,
  Methods: (p: P) => <Base {...p}><path d="M3.2 4.4c2.4-.9 4.6-.6 6.8.9 2.2-1.5 4.4-1.8 6.8-.9v11.2c-2.4-.9-4.6-.6-6.8.9-2.2-1.5-4.4-1.8-6.8-.9z" /><path d="M10 5.3v11.2" /></Base>,
  ArrowRight: (p: P) => <Base {...p}><path d="M4 10h12M11.5 5.5 16 10l-4.5 4.5" /></Base>,
  ArrowLeft: (p: P) => <Base {...p}><path d="M16 10H4M8.5 5.5 4 10l4.5 4.5" /></Base>,
  ChevronDown: (p: P) => <Base {...p}><path d="m5.5 8 4.5 4.5L14.5 8" /></Base>,
  ChevronRight: (p: P) => <Base {...p}><path d="m8 5.5 4.5 4.5L8 14.5" /></Base>,
  Check: (p: P) => <Base {...p}><path d="m4.5 10.4 3.4 3.4 7.6-7.6" /></Base>,
  Download: (p: P) => <Base {...p}><path d="M10 3.5v9M6 8.7l4 4 4-4M4 16.5h12" /></Base>,
  External: (p: P) => <Base {...p}><path d="M11.5 3.5h5v5M16.5 3.5 9.5 10.5M14 11.5v4a1 1 0 0 1-1 1H4.5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h4" /></Base>,
  Info: (p: P) => <Base {...p}><circle cx="10" cy="10" r="7.2" /><path d="M10 9v4.4M10 6.6v.1" /></Base>,
  Alert: (p: P) => <Base {...p}><path d="M10 3.2 17.4 16H2.6z" /><path d="M10 8.2v3.6M10 13.9v.1" /></Base>,
  Close: (p: P) => <Base {...p}><path d="m5 5 10 10M15 5 5 15" /></Base>,
  Menu: (p: P) => <Base {...p}><path d="M3.5 6h13M3.5 10h13M3.5 14h13" /></Base>,
  Sliders: (p: P) => <Base {...p}><path d="M3.5 6h7M14.5 6h2M3.5 14h2M9.5 14h7" /><circle cx="12.5" cy="6" r="2" /><circle cx="7.5" cy="14" r="2" /></Base>,
  Pin: (p: P) => <Base {...p}><path d="M10 17.2s5.2-4.6 5.2-8.6a5.2 5.2 0 1 0-10.4 0c0 4 5.2 8.6 5.2 8.6z" /><circle cx="10" cy="8.6" r="1.8" /></Base>,
  Layers: (p: P) => <Base {...p}><path d="m10 3 7 3.8-7 3.8-7-3.8z" /><path d="m3 10.2 7 3.8 7-3.8M3 13.5l7 3.8 7-3.8" /></Base>,
  Grid: (p: P) => <Base {...p}><rect x="3" y="3" width="14" height="14" rx="1.5" /><path d="M3 10h14M10 3v14" /></Base>,
  Calendar: (p: P) => <Base {...p}><rect x="3" y="4.2" width="14" height="12.6" rx="1.5" /><path d="M3 8h14M7 2.8v2.6M13 2.8v2.6" /></Base>,
  Snow: (p: P) => <Base {...p}><path d="M10 2.5v15M3.5 6.2l13 7.6M16.5 6.2l-13 7.6" /><path d="m8.2 3.8 1.8 1.6 1.8-1.6M8.2 16.2l1.8-1.6 1.8 1.6" /></Base>,
  More: (p: P) => <Base {...p}><circle cx="5" cy="10" r=".9" /><circle cx="10" cy="10" r=".9" /><circle cx="15" cy="10" r=".9" /></Base>,
  Table: (p: P) => <Base {...p}><rect x="3" y="3.5" width="14" height="13" rx="1.5" /><path d="M3 7.8h14M3 12.2h14M8 7.8v8.7" /></Base>,
};

export function Wordmark({ dark = false, className = "" }: { dark?: boolean; className?: string }) {
  const ink = dark ? "#FFFFFF" : "#0B1736";
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 2.6 20.2 7.3v9.4L12 21.4 3.8 16.7V7.3z" stroke={dark ? "#60A5FA" : "#2563EB"} strokeWidth="1.6" strokeLinejoin="round" />
        <path d="M1 12h22" stroke={ink} strokeWidth="1.8" strokeLinecap="round" />
        <path d="M12 2.6V12" stroke={dark ? "#60A5FA" : "#2563EB"} strokeWidth="1.2" strokeLinecap="round" opacity=".55" />
      </svg>
      <span className="text-[17px] font-semibold tracking-[-0.02em]" style={{ color: ink }}>Frostline</span>
    </span>
  );
}
