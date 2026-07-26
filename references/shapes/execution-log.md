# Execution Log Shape Reference

Load before authoring an `execution-log` artifact or changing `examples/execution-log.html`. The compact stub in `SKILL.md` is enough to pick the shape; this file holds the build detail. **The phase strip plus log stream are the shape** — a raw terminal dump is only content.

## Pick This Shape

Use `execution-log` when the source is an observed process:

- Long-running build, release, deploy, migration, CI run, repo sweep, or agent workflow.
- There are phases/plans/checks and event lines.
- Current state matters: branch, commit, changed files, active step, last observation, pass/fail/warn counts.
- The useful question is "what is happening, what is done, what is stuck, and what changed since I last looked?"

If the source is only dated history with no current execution state, use `timeline`. If it is code review, use `developer`. If it is a generic ops inventory with many rows, use `dashboard`.

## Layout

Use the Instrument register: dense sans, mono for timestamps, commits, IDs, paths, and counters.

Required first viewport:

- Compact observed-state bar: live/snapshot state, branch/run name, observed timestamp, and changed-file or job count.
- Hero invariant: one sentence that names the operational truth the run is enforcing.
- Phase strip: 3-6 cards with plan/check ID, title, and state.
- Progress primitive: donut or bar showing approved/done/failed/blocked units.
- Log controls and first log rows visible without scrolling on desktop.

Desktop layout is usually a single 1180-1280px shell. The phase strip can be a horizontal grid; collapse to a stacked strip below 720px. The log table gets horizontal overflow only for the table, never for the whole page.

## Required Data

Normalize the source into explicit state before designing:

```js
const RUN = {
  title: "Branch telemetry",
  observedAt: "2026-07-26 07:40 PDT",
  branch: "codex/example-branch",
  commit: "892806d",
  mode: "snapshot", // "live" | "snapshot" | "paused" | "error"
  changedFiles: 5
};

const PHASES = [
  { id: "PLAN 001", title: "Executable contract", state: "done" },
  { id: "PLAN 002", title: "Exact targeting", state: "running" }
];

const LOGS = [
  { at: "07:40:49", level: "PASS", message: "Working tree clean", detail: "optional payload" }
];
```

Do not make hero stats from artifact production counts ("12 log rows found"). Counts are content only when they describe the underlying execution state: files changed, checks passed, jobs running, plans approved.

## Required Primitives

- `log-stream` for the event table. Load `references/primitives/log-stream.md`.
- `donut` or `bar` for progress. Use the one whose geometry matches the question: donut for share of completion, bar for ordered phase progress.
- Dense ops table conventions for scan-heavy rows: timestamp column, level chip, message, optional detail.
- Optional sparkline only when repeated observations over time matter; do not add one for decoration.

## Interactions

Minimum HTML-native set:

- Search filters messages, IDs, and details with `<mark>` in visible rows.
- Level/status chips toggle categories and have a clear-all path.
- Row expand/collapse reveals payload, command, file list, or diff summary when present.
- Copy snapshot/export produces a text payload with run state and visible rows.

Live mode may use `EventSource` or `fetch` only when the artifact is explicitly meant to observe a local/hosted endpoint. If a live source fails, keep the last snapshot visible and label the status `error` or `stale`; do not quietly freeze the page. Provide a pause/resume tail control if new events can arrive while the reader is inspecting earlier rows.

Self-contained examples should default to static synthetic data. Do not bake private branch names, local paths, log files, hostnames, or access tokens into public examples.

## Visual Rules

- State travels at least three ways: text label, icon/dot shape, and color.
- PASS/WARN/FAIL/INFO chips must remain legible in greyscale.
- Use mono for time and IDs, sans for messages.
- Avoid full-page dark terminal aesthetics unless the source itself is a terminal emulator; render-as-html artifacts stay in the one-truth palette.
- Sticky controls are allowed; sticky log headers are allowed. Do not put the whole log in a fixed-height scrollbox on mobile.

## Copy Snapshot Contract

The copy payload should be useful as a follow-up prompt:

```text
BEGIN ARTIFACT STATE DATA
Run: <title>
Observed: <timestamp>
Visible filters: <filters>
Visible log rows:
- [PASS] 07:40:49 ...
END ARTIFACT STATE DATA

Update <artifact path> to reflect this execution state...
```

The visible fallback textarea is required when clipboard access is blocked.

## Avoid

- A naked `<pre>` dump with no phase/progress context.
- Filters that can hide every row without a clear reset.
- Live-only cues with no timestamp or stale/error state.
- Auto-scrolling that steals position while the reader is inspecting details.
- Hero tiles that count the artifact instead of the execution.
