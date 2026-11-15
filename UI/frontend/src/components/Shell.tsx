import clsx from "clsx";
import { motion } from "motion/react";
import { Dialog } from "radix-ui";
import { useEffect, useState, type ReactNode } from "react";
import { NavLink, Outlet, useLocation } from "react-router";
import { useInv } from "../lib/investigation";
import { InvestigationBar, InvestigationSheetTrigger } from "./Console";
import { Icon, Wordmark } from "./icons";
import { Button } from "./ui";

type Item = { to: string; label: string; icon: (p: any) => ReactNode; short?: string };
export const NAV: { group: string; items: Item[] }[] = [
  { group: "Overview", items: [
    { to: "/", label: "Observatory", icon: Icon.Overview, short: "Home" },
    { to: "/demo", label: "Guided demo", icon: Icon.Play },
  ] },
  { group: "Investigate", items: [
    { to: "/atlas", label: "Atlas", icon: Icon.Atlas },
    { to: "/questions", label: "Questions", icon: Icon.Question },
    { to: "/trends", label: "Trend Detective", icon: Icon.Trend, short: "Trends" },
    { to: "/compare", label: "Compare", icon: Icon.Compare },
    { to: "/corridor", label: "Corridor", icon: Icon.Route },
  ] },
  { group: "Evidence", items: [
    { to: "/evidence", label: "Evidence Engine", icon: Icon.Evidence, short: "Evidence" },
    { to: "/brief", label: "Evidence Brief", icon: Icon.Brief, short: "Brief" },
    { to: "/methods", label: "Methods", icon: Icon.Methods },
  ] },
];
const TABBAR = ["/", "/trends", "/corridor", "/evidence"];
const NO_CONSOLE = new Set(["/", "/methods"]);

function NavItems({ onNavigate, layoutKey }: { onNavigate?: () => void; layoutKey: string }) {
  const { searchFor } = useInv();
  const { pathname } = useLocation();
  return (
    <nav aria-label="Main" className="flex flex-col gap-6">
      {NAV.map((g) => (
        <div key={g.group}>
          <div className="mb-2 px-3 font-mono text-[10.5px] font-medium tracking-[0.12em] text-ink-3 uppercase">{g.group}</div>
          <ul className="flex flex-col gap-0.5">
            {g.items.map((it) => {
              const active = it.to === "/" ? pathname === "/" : pathname.startsWith(it.to);
              const I = it.icon;
              return (
                <li key={it.to}>
                  <NavLink to={{ pathname: it.to, search: searchFor() }} onClick={onNavigate} aria-current={active ? "page" : undefined}
                    className={clsx("relative flex h-9 items-center gap-3 rounded-md px-3 text-[14px] font-medium transition-colors max-lg:h-11",
                      active ? "text-brand-press" : "text-ink-2 hover:bg-[#f1f5fa] hover:text-ink")}>
                    {active && <motion.span layoutId={`nav-active-${layoutKey}`} className="absolute inset-0 rounded-md bg-brand-soft" transition={{ type: "spring", stiffness: 520, damping: 44 }} />}
                    {active && <motion.span layoutId={`nav-bar-${layoutKey}`} className="absolute top-2 bottom-2 -left-3 w-[3px] rounded-r-full bg-brand" transition={{ type: "spring", stiffness: 520, damping: 44 }} />}
                    <I size={18} className={clsx("relative shrink-0", active ? "text-brand" : "text-ink-3")} />
                    <span className="relative">{it.label}</span>
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

function SidebarFooter() {
  const { boot } = useInv();
  return (
    <div className="border-t border-line pt-4 text-[11.5px] leading-[1.6] text-ink-3">
      <div>Data digest <code className="font-mono text-[11px] text-ink-2">{boot.app.digest}</code></div>
      <div>All values from the approved files · no live download</div>
    </div>
  );
}

function MobileMenu() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  useEffect(() => setOpen(false), [pathname]);
  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button variant="ghost" className="size-10 px-0!" aria-label="Open navigation"><Icon.Menu size={20} /></Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-navy/30 backdrop-blur-[2px] data-[state=open]:animate-[fadein_160ms_ease-out]" />
        <Dialog.Content className="fixed inset-y-0 left-0 z-[61] flex w-[300px] max-w-[86vw] flex-col gap-6 overflow-y-auto bg-surface px-5 pt-5 pb-[calc(20px+env(safe-area-inset-bottom))] shadow-[var(--shadow-pop)] data-[state=open]:animate-[fadein_200ms_ease-out]">
          <div className="flex items-center justify-between">
            <Dialog.Title asChild><div><Wordmark /></div></Dialog.Title>
            <Dialog.Close asChild><Button variant="ghost" className="size-10 px-0!" aria-label="Close navigation"><Icon.Close size={18} /></Button></Dialog.Close>
          </div>
          <Dialog.Description className="sr-only">Frostline navigation</Dialog.Description>
          <NavItems layoutKey="drawer" onNavigate={() => setOpen(false)} />
          <div className="mt-auto"><SidebarFooter /></div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function TabBar() {
  const { searchFor } = useInv();
  const { pathname } = useLocation();
  const items = NAV.flatMap((g) => g.items).filter((i) => TABBAR.includes(i.to));
  return (
    <nav aria-label="Primary" className="fixed inset-x-0 bottom-0 z-50 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md md:hidden">
      <ul className="mx-auto flex max-w-lg">
        {items.map((it) => {
          const active = it.to === "/" ? pathname === "/" : pathname.startsWith(it.to);
          const I = it.icon;
          return (
            <li key={it.to} className="flex-1">
              <NavLink to={{ pathname: it.to, search: searchFor() }} aria-current={active ? "page" : undefined}
                className={clsx("flex h-16 flex-col items-center justify-center gap-1 text-[11px] font-medium", active ? "text-brand" : "text-ink-3")}>
                <I size={22} />{it.short ?? it.label}
              </NavLink>
            </li>
          );
        })}
        <li className="flex-1">
          <NavLink to={{ pathname: "/brief", search: searchFor() }} aria-current={pathname.startsWith("/brief") ? "page" : undefined}
            className={clsx("flex h-16 flex-col items-center justify-center gap-1 text-[11px] font-medium", pathname.startsWith("/brief") ? "text-brand" : "text-ink-3")}>
            <Icon.Brief size={22} />Brief
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}

export function Footer() {
  const { boot } = useInv();
  return (
    <footer className="mt-20 border-t border-line pt-6 pb-2 text-[12px] leading-[1.7] text-ink-3">
      <p className="max-w-[100ch]">
        <b className="font-medium text-ink-2">{boot.app.name} by {boot.app.team}</b> · NASA Space Apps Challenge 2026, Be An Earth System Trend Detective! · An exploratory scientific
        investigation tool. It does not assess road safety, measure ice or predict opening dates, and it makes no statement of cause. Built with AI assistance; see Methods and
        sources for the disclosure. NASA does not endorse this project.
      </p>
    </footer>
  );
}

export function Shell() {
  const { pathname } = useLocation();
  const { boot } = useInv();
  const showConsole = !NO_CONSOLE.has(pathname);
  const fullBleed = pathname === "/";
  useEffect(() => { window.scrollTo({ top: 0 }); }, [pathname]);
  return (
    <div className="min-h-dvh">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:rounded-md focus:bg-surface focus:px-4 focus:py-2 focus:shadow-[var(--shadow-pop)]">Skip to content</a>

      {/* desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[256px] flex-col gap-8 border-r border-line bg-surface px-5 pt-6 pb-5 lg:flex">
        <div>
          <NavLink to={{ pathname: "/" }} aria-label="Frostline home"><Wordmark /></NavLink>
          <div className="mt-2 pl-[2px] text-[12px] leading-[1.5] text-ink-3"><span className="font-medium text-ink-2">by {boot.app.team}</span><br />{boot.app.tagline}</div>
        </div>
        <div className="-mx-1 flex-1 overflow-y-auto px-1"><NavItems layoutKey="side" /></div>
        <SidebarFooter />
      </aside>

      {/* tablet and phone header */}
      <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-line bg-surface/90 px-3 backdrop-blur-md lg:hidden">
        <div className="flex items-center gap-1"><MobileMenu /><NavLink to={{ pathname: "/" }} aria-label="Frostline home"><Wordmark /></NavLink></div>
        <span className="pr-2 text-[12px] text-ink-3">by {boot.app.team}</span>
      </header>

      <div className="lg:pl-[256px]">
        {showConsole && (
          <div className="sticky top-14 z-30 border-b border-line bg-canvas/85 backdrop-blur-md lg:top-0">
            <div className="mx-auto max-w-[1240px] px-4 py-3 sm:px-6 lg:px-10 lg:py-4">
              <InvestigationBar />
              <InvestigationSheetTrigger />
            </div>
          </div>
        )}
        <main id="main" className={clsx("mx-auto max-w-[1240px] px-4 pb-28 sm:px-6 md:pb-12 lg:px-10", fullBleed ? "pt-0" : "pt-8 lg:pt-10")}>
          <motion.div key={pathname} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.28, ease: [0.2, 0.7, 0.2, 1] }}>
            <Outlet />
          </motion.div>
          <Footer />
        </main>
      </div>
      <TabBar />
    </div>
  );
}
