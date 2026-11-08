// Keep fiscal readers/checkers independent. This guards the tool, not their logic.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const POLICY = {
  path: ['builder', 'scripts', 'tests'], format: ['python'],
  minLines: 5, minTokens: 50, maxLines: 100000, maxSize: '5mb',
  mode: 'weak', threshold: 0.5, reporters: ['console', 'json'],
  output: 'reports/duplication',
};

function collectSources(root) {
  const { Tokenizer } = require('@jscpd/tokenizer');
  const { getModeHandler } = require('@jscpd/core');
  const tokenizer = new Tokenizer();
  const options = { ...POLICY, mode: getModeHandler(POLICY.mode) };
  const sources = [];
  function visit(directory) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const filePath = path.join(directory, entry.name);
      assert.ok(!entry.isSymbolicLink(), `Symlink in maintained source: ${filePath}`);
      if (entry.isDirectory()) visit(filePath);
      else if (entry.isFile() && entry.name.endsWith('.py')) {
        const bytes = fs.readFileSync(filePath);
        const content = bytes.toString('utf8');
        const lineCount = content.split('\n').length;
        assert.ok(bytes.length <= 5 * 1024 * 1024, `Source exceeds maxSize: ${filePath}`);
        assert.ok(lineCount <= POLICY.maxLines, `Source exceeds maxLines: ${filePath}`);
        assert.ok(!content.includes('jscpd:ignore'), `Suppression in source: ${filePath}`);
        // jscpd's five-line file minimum and tokenless-file behavior are retained.
        if (lineCount >= POLICY.minLines) {
          const maps = tokenizer.generateMaps(filePath, content, 'python', options);
          if (maps.length) sources.push(filePath);
        }
      }
    }
  }
  for (const directory of POLICY.path) visit(path.join(root, directory));
  assert.ok(sources.length > 0, 'No eligible maintained Python sources');
  return sources.sort();
}

function validateReport(report, expectedFiles, root) {
  const { total, formats } = report.statistics;
  assert.deepEqual(Object.keys(formats), ['python'], 'Unexpected report formats');
  const sources = formats.python.sources;
  const actualFiles = Object.keys(sources).map((name) => path.resolve(root, name)).sort();
  assert.deepEqual(actualFiles, expectedFiles.map((name) => path.resolve(root, name)).sort(),
    'Incomplete or unexpected source population');
  for (const value of [total.lines, total.duplicatedLines, total.sources]) {
    assert.ok(Number.isSafeInteger(value) && value >= 0, 'Invalid report counts');
  }
  assert.ok(total.lines > 0 && total.sources > 0, 'Empty duplication report');
  assert.equal(total.sources, actualFiles.length, 'Incorrect source count');
  let lines = 0;
  for (const source of Object.values(sources)) {
    assert.ok(Number.isSafeInteger(source.lines) && source.lines >= 0, 'Invalid source lines');
    lines += source.lines;
  }
  assert.equal(total.lines, lines, 'Incorrect line denominator');
  assert.equal(formats.python.total.lines, total.lines, 'Inconsistent format totals');
  assert.equal(formats.python.total.duplicatedLines, total.duplicatedLines);
  // jscpd rounds its display percentage. Enforce the same 0.5% budget without rounding.
  return BigInt(total.duplicatedLines) * 200n > BigInt(total.lines) ? 1 : 0;
}

function checkDuplicates(root, run = spawnSync) {
  try {
    const reportPath = path.join(root, POLICY.output, 'jscpd-report.json');
    // A failed tool/config invocation must never reuse a previous successful report.
    fs.rmSync(reportPath, { force: true });
    assert.equal(process.versions.node.split('.')[0], '22', 'Project tooling requires Node 22');
    const config = JSON.parse(fs.readFileSync(path.join(root, '.jscpd.json'), 'utf8'));
    assert.deepEqual(config, POLICY, 'Duplication settings differ from the reviewed policy');
    const manifestPath = path.join(root, 'package.json');
    if (fs.existsSync(manifestPath)) {
      const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
      assert.ok(!Object.hasOwn(manifest, 'jscpd'), 'Secondary package.json jscpd config is forbidden');
    }
    const expectedFiles = collectSources(root);
    const result = run(process.execPath, [
      path.resolve(__dirname, '../node_modules/jscpd/bin/jscpd'),
      '--config', path.join(root, '.jscpd.json'),
    ], { cwd: root, stdio: 'inherit', timeout: 120000 });
    assert.ok(!result.error && !result.signal && [0, 1].includes(result.status),
      'jscpd tool execution failed');
    const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    const status = validateReport(report, expectedFiles, root);
    assert.ok(result.status === 0 || status === 1, 'jscpd failed without a budget violation');
    const { duplicatedLines, lines, sources } = report.statistics.total;
    console.log(`Duplication: ${duplicatedLines}/${lines} lines ` +
      `(${(100 * duplicatedLines / lines).toFixed(4)}%), ${sources} files; budget 0.5%`);
    return status;
  } catch (error) {
    console.error(`Duplication analysis error: ${error.message}`);
    return 2;
  }
}

if (require.main === module) process.exitCode = checkDuplicates(process.cwd());
module.exports = { checkDuplicates, validateReport };
