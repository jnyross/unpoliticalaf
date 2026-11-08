const assert = require("node:assert/strict");
const test = require("node:test");
const publish = require("../scripts/release_notes.cjs");

function fixture({tag = "v2.0.0", releases = [], existing, lookupError = 404,
                  comparison = "ahead", mainComparison = "ahead", commits = [], pulls = [], fail} = {}) {
  const calls = [];
  function method(name, value) {
    return async params => {
      calls.push({name, params});
      if (name === fail) throw new Error(`${name} failed`);
      return {data: value};
    };
  }
  const repos = {
    getReleaseByTag: async params => {
      calls.push({name: "getReleaseByTag", params});
      if (existing) return {data: existing};
      throw Object.assign(new Error("lookup"), {status: lookupError});
    },
    listReleases: method("listReleases", releases),
    compareCommitsWithBasehead: async params => {
      const name = params.basehead.endsWith("...main") ? "main" : "compare";
      return method(name, {status: name === "main" ? mainComparison : comparison})(params);
    },
    generateReleaseNotes: method("generate", {body: "Version-only changes"}),
    listCommits: method("commits", commits),
    createRelease: method("create", {html_url: "https://example.invalid/version"})
  };
  const github = {rest: {repos, pulls: {list: method("pulls", pulls)}},
    paginate: async (fn, params) => (await fn(params)).data};
  const context = {repo: {owner: "owner", repo: "repo"}, ref: `refs/tags/${tag}`};
  const core = {info() {}, notice() {}};
  return {calls, run: () => publish({github, context, core})};
}

const version = (tagName = "v1.0.0", extra = {}) => ({tag_name: tagName, draft: false, prerelease: false, ...extra});
const pull = (number, mergeCommitSha, extra = {}) => ({
  number, merge_commit_sha: mergeCommitSha, merged_at: "2026-11-01", title: `Change ${number}`,
  user: {login: "contributor"}, ...extra
});

test("site snapshots never become a stable version's notes baseline", async () => {
  const f = fixture({releases: [version("site-" + "a".repeat(40)), version("v2.0.0-rc.1", {prerelease: true}),
    version("v1.5.0", {draft: true}), version()]});
  await f.run();
  assert.equal(f.calls.find(c => c.name === "generate").params.previous_tag_name, "v1.0.0");
  assert.deepEqual(f.calls.filter(c => c.name === "compare").map(c => c.params.basehead), ["v1.0.0...v2.0.0"]);
  const release = f.calls.find(c => c.name === "create").params;
  assert.equal(release.tag_name, "v2.0.0");
  assert.equal(release.body, "Version-only changes");
  assert.equal(release.make_latest, "true");
  assert.equal(release.prerelease, false);
});

test("first version includes full tagged history despite newer site snapshots", async () => {
  const f = fixture({releases: [version("site-" + "a".repeat(40))],
    commits: [{sha: "merged"}, {sha: "older"}],
    pulls: [pull(7, "merged"), pull(3, "older"), pull(9, "future"),
      pull(8, "merged", {merged_at: null})]});
  await f.run();
  assert.equal(f.calls.some(c => c.name === "generate"), false);
  const body = f.calls.find(c => c.name === "create").params.body;
  assert.match(body, /Change 3 by @contributor in #3/);
  assert.match(body, /Change 7 by @contributor in #7/);
  assert.doesNotMatch(body, /Change (8|9)/);
  assert.ok(body.indexOf("#3") < body.indexOf("#7"));
  assert.match(body, /\/commits\/v2\.0\.0/);
});

test("prerelease notes may use a previous prerelease but never claim latest", async () => {
  const f = fixture({tag: "v2.0.0-rc.2", releases: [version("v2.0.0-rc.1", {prerelease: true})]});
  await f.run();
  assert.equal(f.calls.find(c => c.name === "generate").params.previous_tag_name, "v2.0.0-rc.1");
  assert.equal(f.calls.find(c => c.name === "create").params.make_latest, "false");
});

test("out-of-line version releases cannot become comparison boundaries", async () => {
  for (const comparison of ["behind", "diverged"]) {
    const f = fixture({releases: [version("v9.0.0")], comparison});
    await f.run();
    assert.equal(f.calls.some(c => c.name === "generate"), false);
    assert.ok(f.calls.some(c => c.name === "commits"));
  }
});

test("published or draft existing versions retain their notes and status", async () => {
  for (const draft of [true, false]) {
    const f = fixture({existing: {html_url: "existing", draft}});
    await f.run();
    assert.deepEqual(f.calls.map(c => c.name), ["main", "getReleaseByTag"]);
  }
});

test("lookup, pagination, comparison and generation failures never create a release", async () => {
  for (const lookupError of [401, 403, 429, 500]) {
    const f = fixture({lookupError});
    await assert.rejects(f.run());
    assert.equal(f.calls.some(c => c.name === "create"), false);
  }
  for (const fail of ["main", "listReleases", "compare", "generate", "commits", "pulls"]) {
    const f = fixture({fail, releases: ["compare", "generate"].includes(fail) ? [version()] : []});
    await assert.rejects(f.run(), /failed/);
    assert.equal(f.calls.some(c => c.name === "create"), false);
  }
});

test("creation failures propagate without a success notice", async () => {
  const f = fixture({fail: "create"});
  await assert.rejects(f.run(), /create failed/);
});

test("version publisher rejects deployment snapshot tags before any API calls", async () => {
  for (const tag of ["site-" + "a".repeat(40), "main", "v-no-version"]) {
    const f = fixture({tag});
    await assert.rejects(f.run(), /Only version tags/);
    assert.equal(f.calls.length, 0);
  }
});

test("code-like version tag text is handled only as data", async () => {
  const tag = "v1.0.0-${process.exit(99)}";
  const f = fixture({tag});
  await f.run();
  assert.equal(f.calls.find(c => c.name === "create").params.tag_name, tag);
});

test("version tags outside main ancestry fail before release writes, including retries", async () => {
  for (const mainComparison of ["behind", "diverged", "unknown"]) {
    for (const existing of [undefined, {html_url: "existing", draft: true}]) {
      const f = fixture({mainComparison, existing});
      await assert.rejects(f.run(), /main ancestry/);
      assert.deepEqual(f.calls.map(c => c.name), ["main"]);
    }
  }
});

test("an identical main tag is accepted", async () => {
  const f = fixture({mainComparison: "identical"});
  await f.run();
  assert.equal(f.calls.find(c => c.name === "main").params.basehead, "v2.0.0...main");
  assert.ok(f.calls.some(c => c.name === "create"));
});

test("stable notes exclude prerelease tags even if their metadata is wrong", async () => {
  const f = fixture({releases: [version("v1.9.0-rc.1"), version()]});
  await f.run();
  assert.equal(f.calls.find(c => c.name === "generate").params.previous_tag_name, "v1.0.0");
});
