// Version checkpoints and deployment snapshots share GitHub Releases, not history
// boundaries. Never let a site-<sha> release shorten a version's changelog.
module.exports = async function publish({github, context, core}) {
  const {owner, repo} = context.repo;
  const tag = context.ref.slice("refs/tags/".length);
  if (!context.ref.startsWith("refs/tags/v") || !/^v[0-9]/.test(tag)) {
    throw new Error("Only version tags can publish version release notes");
  }
  try {
    const existing = await github.rest.repos.getReleaseByTag({owner, repo, tag});
    core.info(`Release already exists: ${existing.data.html_url}; leaving it unchanged.`);
    return;
  } catch (error) {
    if (error.status !== 404) throw error;
  }

  const prerelease = tag.includes("-");
  const releases = await github.paginate(github.rest.repos.listReleases, {owner, repo, per_page: 100});
  // GitHub returns releases newest first. Only published version releases in the
  // target's ancestry are eligible; stable checkpoints exclude prereleases.
  let previous;
  for (const candidate of releases) {
    if (candidate.draft || !/^v[0-9]/.test(candidate.tag_name) ||
        candidate.tag_name === tag || (!prerelease && candidate.prerelease)) continue;
    const comparison = await github.rest.repos.compareCommitsWithBasehead({
      owner, repo, basehead: `${candidate.tag_name}...${tag}`, per_page: 1
    });
    if (["ahead", "identical"].includes(comparison.data.status)) {
      previous = candidate.tag_name;
      break;
    }
  }

  let body;
  if (previous) {
    const notes = await github.rest.repos.generateReleaseNotes({
      owner, repo, tag_name: tag, previous_tag_name: previous
    });
    body = notes.data.body;
  } else {
    // With no prior version, GitHub's implicit baseline might be a site snapshot.
    // Build the initial full-history list from PRs whose merge commits actually
    // belong to this tag, rather than silently omitting most of the history.
    const commits = await github.paginate(github.rest.repos.listCommits,
      {owner, repo, sha: tag, per_page: 100});
    const ancestry = new Set(commits.map(commit => commit.sha));
    const pulls = await github.paginate(github.rest.pulls.list,
      {owner, repo, state: "closed", base: "main", per_page: 100});
    const included = pulls.filter(pr => pr.merged_at && ancestry.has(pr.merge_commit_sha))
      .sort((a, b) => a.number - b.number);
    const lines = included.map(pr =>
      `* ${pr.title.replace(/[\r\n]/g, " ")} by @${pr.user.login} in #${pr.number}`);
    body = ["## What's Changed", "", ...lines, "",
      `**Full history**: https://github.com/${owner}/${repo}/commits/${encodeURIComponent(tag)}`].join("\n");
  }

  const release = await github.rest.repos.createRelease({
    owner, repo, tag_name: tag, name: tag, body, prerelease,
    make_latest: prerelease ? "false" : "legacy"
  });
  core.notice(`Published release notes: ${release.data.html_url}`);
};
