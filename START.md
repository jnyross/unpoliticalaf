# Start UnpoliticalAF

## What exists, and what does not

This workspace contains readiness instructions for a separate project. Read
`README.md`, `AUTONOMOUS-BRIEF.md` and `AGENTS.md` together. No app stack is approved;
there is no application run command yet. These documents do **not** create a team,
manager, scheduled worker or deployed application. No team was started by this
setup. Current blocker: a person must establish a native manager through `/teams`
and hand over the brief; this setup conversation has no manager tools.

## Minimal native-team activation handover (instructions only)

Do this only when ready to start agent work and its usage. Do not install anything,
edit CodeAF configuration or change approval/billing/wake settings for these steps.

1. Open/select the CodeAF workspace `/home/john/projects/unpoliticalaf` (not the
   sister project). Open `/teams` or press `alt+2`.
2. Choose **+ New AI team** in the Teams sidebar. Enter **UnpoliticalAF**, choose a
   colour, leave members empty and press **enter** to create. Creating an empty
   team does not create a manager or start its members.
3. On that team choose **+ AI manager**, which creates a manager conversation in
   the team's folder. If that control is not available in the current layout, use
   **+ Add chat** → **+ New conversation**, give it the assignment below and
   **enter create**, then return to Teams → **Choose AI manager** and select that
   conversation. The Add chat route submits its assignment before appointment,
   so the assignment explicitly prohibits starting work until manager status is
   confirmed. Do not select **All teams**: this needs a project manager, not a
   global one. Confirm the chosen conversation shows **◆ Manager**.
4. Send the following handover (or use it as the new conversation assignment).
   The first action must verify the working directory; if it is wrong, stop and
   correct the project selection through the UI before any edits or member starts.
   Do not assume team creation or a project name proves the folder.

   > Act as delivery lead for UnpoliticalAF only after your native manager status
   > is confirmed. First verify your working directory is exactly
   > /home/john/projects/unpoliticalaf; stop if not. Read README.md,
   > AUTONOMOUS-BRIEF.md, AGENTS.md and START.md there. Follow their scope,
   > independent-review gates and approval boundaries. Use your native manager
   > tools to start three separate members: fiscal-data researcher,
   > implementation, and independent QA/data reviewer, with precise ownership
   > and evidence deliverables from AGENTS.md. Keep the reviewer independent.
   > Record actual member handles and status; do not invent running state.
   > Research and plan the bounded first usable version covering expenditure
   > and tax revenue, then request approval for the proposed stack before adopting
   > it. Routine local reversible choices within the approved brief are delegated.
   > No commits, remotes, publication/deployment, installations, factory activation,
   > configuration/settings/subscription changes or schedules are authorized.
   > Report your real roster, first scoped tickets and any blocking decisions.

5. Inspect the manager's **Traffic** and actual roster. Member starts use
   `team_start` under the existing approval posture: approve only permitted starts
   if asked. New conversations consume usage; the manager cannot grant your
   permissions. A member being created does not prove it ran: auto-wake may be
   off, starts may be refused by a cap, or a permission may await you. With wake
   off, open/resume the member to receive its brief; do not silently change settings.
   Starting a member requires a window holding the manager. Verify researcher,
   implementation and reviewer each received their brief in the correct folder.

Use `alt+m` to return to the manager. Ask it for meaningful results, evidence and
blocked decisions, not a promise of unlimited unattended execution. Native wake
limits and user permissions can require you to resume or answer. Stop at the local
accepted candidate; release/publication requires separate approval.

## Evidence before calling a build complete

The manager must supply the acceptance mapping and independent signed-off review
specified in `AGENTS.md`: official source traceability and reconciled figures for
both spending and tax, real end-to-end checks, mobile/keyboard accessibility,
exact candidate identity, commands/results, limitations and local reproduction.
No tests or build success are claimed by this readiness document. Before handover,
inspect `git status --short` and the four documents; no commit is required.

## Authority checked

UI labels and lifecycle are from CodeAF's `team-manager` and `teams-page` manual;
these pages were read, including team creation, manager assignment, membership
and settings sections. Saved prior manual output paths and the skill/component
guide paths are listed in `AGENTS.md`. The separate software-factory workflow was
read only: it is not installed/activated/configured by these instructions, nor
is its GitHub/T3/Vercel profile selected for this project.
