// Read the actual workflow contracts, not a parallel list of expected triggers.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const workflow = name => fs.readFileSync(path.join(root, ".github/workflows", name), "utf8");
const source = workflow("release.yml");
const names = JSON.parse(source.match(/^\s+workflows: (\[.*\])$/m)[1]);
const condition = source.match(/    if: >-\n([\s\S]*?)\n    runs-on:/)[1].trim();

function accepted(name, overrides = {}) {
  const run = {name, conclusion: "success", head_branch: "main", event: "push",
    head_repository: {full_name: "owner/repo"}, ...overrides};
  // The workflow_run selector is checked independently of the job expression.
  return names.includes(name) && vm.runInNewContext(condition, {
    github: {repository: "owner/repo", event: {workflow_run: run}},
    fromJSON: JSON.parse, contains: (values, value) => values.includes(value)
  });
}

test("routine pushes, schedules and auto-merge dispatches all reach the release", () => {
  const routine = fs.existsSync(path.join(root, ".github/workflows/deploy.yml")) ? "deploy.yml" : "live.yml";
  const name = workflow(routine).match(/^name: (.+)$/m)[1];
  for (const event of ["push", "schedule", "workflow_dispatch"]) {
    assert.equal(accepted(name, {event}), true, `${routine}: ${event}`);
  }
  const dispatch = workflow("auto-merge.yml").match(/workflow_id: "(live|deploy)\.yml", ref: "main"/)[1] + ".yml";
  const dispatchName = workflow(dispatch).match(/^name: (.+)$/m)[1];
  assert.equal(accepted(dispatchName, {event: "workflow_dispatch"}), true);
});

test("both deployment names use the same safe release gate through the migration", () => {
  for (const name of ["Verify and record production deployment", "Live site matches main"]) {
    assert.equal(accepted(name), true);
    for (const conclusion of ["failure", "cancelled", "skipped", "neutral", "timed_out"]) {
      assert.equal(accepted(name, {conclusion}), false);
    }
    assert.equal(accepted(name, {head_branch: "feature"}), false);
    assert.equal(accepted(name, {head_repository: {full_name: "fork/repo"}}), false);
    assert.equal(accepted(name, {event: "pull_request"}), false);
  }
  assert.equal(accepted("Build and check"), false);
});

test("duplicate entry points serialize by commit and checkout exactly that SHA", () => {
  assert.match(source, /group: site-release-\$\{\{ github.event.workflow_run.head_sha \}\}/);
  assert.match(source, /cancel-in-progress: false/);
  assert.match(source, /ref: \$\{\{ github.event.workflow_run.head_sha \}\}/);
  assert.match(source, /persist-credentials: false/);
  assert.match(source, /branches: \[main\]/);
});

test("version notes and site snapshots cannot trigger or overwrite each other", () => {
  assert.match(workflow("release-notes.yml"), /tags: \["v\[0-9\]\*"\]/);
  assert.doesNotMatch(workflow("release-notes.yml"), /workflow_run:/);
  assert.doesNotMatch(source, /tags:/);
  const publisher = fs.readFileSync(path.join(root, "scripts/publish_release.sh"), "utf8");
  assert.match(publisher, /tag="site-\$COMMIT"/);
  assert.match(publisher, /--draft=false --latest=false/);
});
