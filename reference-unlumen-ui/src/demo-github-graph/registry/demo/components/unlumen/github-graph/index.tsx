"use client";

import * as React from "react";

import {
  GithubGraph,
  normalizeGithubAccount,
  type GithubGraphProps,
} from "@/components/unlumen-ui/github-graph";

type GithubGraphDemoProps = Pick<
  GithubGraphProps,
  | "variant"
  | "animation"
  | "animationSpeed"
  | "cellSize"
  | "cellGap"
  | "cellRadius"
  | "showLegend"
  | "ambientEffect"
  | "ambientIntensity"
> & {
  months?: number | string;
};

export function GithubGraphDemo({
  variant = "github",
  animation = "wave",
  animationSpeed = 1,
  cellSize = 18,
  cellGap = 4,
  cellRadius = 3,
  showLegend = false,
  ambientEffect = "twinkle",
  ambientIntensity = 0.65,
  months = 6,
}: GithubGraphDemoProps) {
  const [draftAccount, setDraftAccount] = React.useState("shadcn");
  const [account, setAccount] = React.useState("shadcn");
  const [error, setError] = React.useState<string | null>(null);
  const resolvedMonths = Number(months) || 6;

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextAccount = normalizeGithubAccount(draftAccount);

    if (!nextAccount) {
      setError("Enter a valid GitHub username.");
      return;
    }

    setError(null);
    setDraftAccount(nextAccount);
    setAccount(nextAccount);
  };

  return (
    <div className="flex w-full justify-center p-4 sm:p-6">
      <div className="w-fit max-w-full">
        <form onSubmit={submit} className="mb-5">
          <div className="flex items-baseline gap-0.5 text-lg font-medium tracking-tight text-foreground">
            <span aria-hidden="true">@</span>
            <label htmlFor="github-graph-account" className="sr-only">
              GitHub username
            </label>
            <input
              id="github-graph-account"
              value={draftAccount}
              onChange={(event) => setDraftAccount(event.target.value)}
              placeholder="github"
              aria-invalid={error ? true : undefined}
              className="w-[11ch] border-0 bg-transparent p-0 text-lg font-medium tracking-tight outline-none placeholder:text-muted-foreground focus-visible:text-foreground"
            />
          </div>
          {error && <p className="mt-1 text-xs text-destructive">{error}</p>}
        </form>

        <GithubGraph
          account={account}
          months={resolvedMonths}
          variant={variant}
          animation={animation}
          animationSpeed={animationSpeed}
          cellSize={cellSize}
          cellGap={cellGap}
          cellRadius={cellRadius}
          showLegend={showLegend}
          ambientEffect={ambientEffect}
          ambientIntensity={ambientIntensity}
          showAccount={false}
        />
      </div>
    </div>
  );
}
