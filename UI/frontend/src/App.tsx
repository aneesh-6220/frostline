import { MotionConfig } from "motion/react";
import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, Outlet, RouterProvider } from "react-router";
import { Shell } from "./components/Shell";
import { Wordmark } from "./components/icons";
import { ErrorState, LoadingBlock } from "./components/ui";
import { useBootstrap } from "./lib/api";
import { InvestigationProvider } from "./lib/investigation";
import { Observatory } from "./views/Observatory";

const Demo = lazy(() => import("./views/Demo"));
const Atlas = lazy(() => import("./views/Atlas"));
const Questions = lazy(() => import("./views/Questions"));
const Detective = lazy(() => import("./views/Detective"));
const Compare = lazy(() => import("./views/Compare"));
const Corridor = lazy(() => import("./views/Corridor"));
const Evidence = lazy(() => import("./views/Evidence"));
const Brief = lazy(() => import("./views/Brief"));
const Methods = lazy(() => import("./views/Methods"));
const NotFound = lazy(() => import("./views/NotFound"));

function Root() {
  const boot = useBootstrap();
  if (boot.isError) {
    return (
      <div className="mx-auto flex min-h-dvh max-w-xl flex-col justify-center gap-6 px-6">
        <Wordmark />
        <ErrorState error={boot.error} />
        <p className="text-[13px] text-ink-3">Frostline cannot start. Restore the data with <code className="font-mono">python3 -I scripts/regenerate_all.py</code> and make sure the API is running.</p>
      </div>
    );
  }
  if (!boot.data) {
    return (
      <div className="grid min-h-dvh place-items-center" role="status" aria-label="Loading Frostline">
        <div className="flex flex-col items-center gap-4"><Wordmark /><div className="h-[3px] w-40 overflow-hidden rounded-full bg-line"><div className="skeleton h-full w-full" /></div></div>
      </div>
    );
  }
  return (
    <InvestigationProvider boot={boot.data}>
      <Outlet />
    </InvestigationProvider>
  );
}

const page = (el: ReactNode) => <Suspense fallback={<LoadingBlock height={420} />}>{el}</Suspense>;

const router = createBrowserRouter([
  {
    element: <Root />,
    children: [
      {
        element: <Shell />,
        children: [
          { index: true, element: <Observatory /> },
          { path: "demo", element: page(<Demo />) },
          { path: "atlas", element: page(<Atlas />) },
          { path: "questions", element: page(<Questions />) },
          { path: "trends", element: page(<Detective />) },
          { path: "compare", element: page(<Compare />) },
          { path: "corridor", element: page(<Corridor />) },
          { path: "evidence", element: page(<Evidence />) },
          { path: "brief", element: page(<Brief />) },
          { path: "methods", element: page(<Methods />) },
          { path: "*", element: page(<NotFound />) },
        ],
      },
    ],
  },
]);

export function App() {
  return (
    <MotionConfig reducedMotion="user">
      <RouterProvider router={router} />
    </MotionConfig>
  );
}
