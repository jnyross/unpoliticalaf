const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');
const { checkDuplicates, validateReport } = require('../scripts/check_duplicates.cjs');

const ROOT = path.resolve(__dirname, '..');
const CONFIG = JSON.parse(fs.readFileSync(path.join(ROOT, '.jscpd.json'), 'utf8'));
const BLOCK = Array.from({ length: 15 }, (_, index) =>
  `    result_${index} = calculate_${index}(input_value, ${index * 29})`
).join('\n');
const SOURCE = `def calculate_values(input_value):\n${BLOCK}\n    return result_14\n`;

function fixture(context) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'duplication-'));
  context.after(() => fs.rmSync(root, { recursive: true, force: true }));
  for (const directory of CONFIG.path) fs.mkdirSync(path.join(root, directory));
  fs.writeFileSync(path.join(root, '.jscpd.json'), JSON.stringify(CONFIG));
  fs.writeFileSync(path.join(root, 'builder', 'original.py'), SOURCE);
  return root;
}

function report(lines, duplicatedLines) {
  const total = { lines, duplicatedLines, sources: 1, clones: 0 };
  return {
    statistics: {
      total,
      formats: { python: { total, sources: { 'builder/original.py': total } } },
    },
    duplicates: [],
  };
}

test('keeps the original settings and coherent pinned Node lock', () => {
  assert.deepEqual(CONFIG, {
    path: ['builder', 'scripts', 'tests'], format: ['python'],
    minLines: 5, minTokens: 50, maxLines: 100000, maxSize: '5mb',
    mode: 'weak', threshold: 0.5, reporters: ['console', 'json'],
    output: 'reports/duplication',
  });
  const manifest = require('../package.json');
  const lock = require('../package-lock.json');
  assert.equal(manifest.devDependencies.jscpd, '4.0.5');
  assert.deepEqual(lock.packages[''].devDependencies, manifest.devDependencies);
  assert.equal(lock.packages['node_modules/jscpd'].version, '4.0.5');
});

test('raw budget accepts equality and rejects excess hidden by rounding', () => {
  const expected = ['builder/original.py'];
  assert.equal(validateReport(report(200000, 1000), expected, ROOT), 0);
  assert.equal(validateReport(report(200000, 1001), expected, ROOT), 1);
});

test('rejects empty, malformed and incomplete report populations', () => {
  for (const invalid of [{}, report(0, 0), report(200, -1), report(200, NaN)]) {
    assert.throws(() => validateReport(invalid, ['builder/original.py'], ROOT));
  }
  assert.throws(() => validateReport(report(200, 0), ['tests/missing.py'], ROOT));
  const invalid = report(200, 0);
  invalid.statistics.total = { ...invalid.statistics.total, lines: 201 };
  assert.throws(() => validateReport(invalid, ['builder/original.py'], ROOT));
});

test('real locked jscpd passes unique code and excludes generated/publisher trees', (context) => {
  const root = fixture(context);
  for (const directory of ['site', 'data', 'reference', 'quality']) {
    fs.mkdirSync(path.join(root, directory));
    fs.writeFileSync(path.join(root, directory, 'copy.py'), SOURCE.repeat(8));
  }
  assert.equal(checkDuplicates(root), 0);
  const result = JSON.parse(fs.readFileSync(
    path.join(root, CONFIG.output, 'jscpd-report.json'), 'utf8'
  ));
  assert.equal(result.statistics.total.sources, 1);
  assert.equal(result.statistics.total.duplicatedLines, 0);
});

for (const directory of ['builder', 'scripts', 'tests/nested']) {
  test(`real duplicated blocks in ${directory} fail and retain a report`, (context) => {
    const root = fixture(context);
    const target = path.join(root, directory);
    fs.mkdirSync(target, { recursive: true });
    fs.writeFileSync(path.join(target, 'copy.py'), SOURCE);
    assert.equal(checkDuplicates(root), 1);
    const result = JSON.parse(fs.readFileSync(
      path.join(root, CONFIG.output, 'jscpd-report.json'), 'utf8'
    ));
    assert.ok(result.duplicates.length > 0);
    assert.equal(result.statistics.total.sources, 2);
  });
}

test('weak mode ignores changed comments and whitespace, not duplicate code', (context) => {
  const root = fixture(context);
  const copy = SOURCE.split('\n').map((line) => ` ${line}  # changed comment`).join('\n');
  fs.writeFileSync(path.join(root, 'tests', 'copy.py'), copy);
  assert.equal(checkDuplicates(root), 1);
});

test('real duplicates within one file also fail', (context) => {
  const root = fixture(context);
  fs.writeFileSync(path.join(root, 'builder', 'original.py'), SOURCE.repeat(2));
  assert.equal(checkDuplicates(root), 1);
});

test('real matching blocks below the five-line or 50-token minimum do not fail', (context) => {
  const root = fixture(context);
  for (const content of [
    'a = 1\nb = 2\nc = 3\nd = 4\ne = 5\nf = 6\n',
    `def compact(value):\n    return (${Array.from(
      { length: 70 }, (_, index) => `value + ${index}`
    ).join(' + ')})\n\n\n`,
  ]) {
    fs.writeFileSync(path.join(root, 'builder', 'original.py'), content);
    fs.writeFileSync(path.join(root, 'tests', 'copy.py'), content);
    assert.equal(checkDuplicates(root), 0);
    const result = JSON.parse(fs.readFileSync(
      path.join(root, CONFIG.output, 'jscpd-report.json'), 'utf8'
    ));
    assert.equal(result.statistics.total.sources, 2);
    assert.equal(result.duplicates.length, 0);
  }
});

test('preserves jscpd short-file and tokenless rules without hiding nested modules', (context) => {
  const root = fixture(context);
  fs.mkdirSync(path.join(root, 'builder', 'data'));
  fs.writeFileSync(path.join(root, 'builder', 'data', 'small.py'), 'value = 1\n');
  fs.writeFileSync(path.join(root, 'tests', 'comments.py'), '# comment\n'.repeat(10));
  assert.equal(checkDuplicates(root), 0);
});

test('missing or malformed config cannot fall back to a successful default scan', (context) => {
  const root = fixture(context);
  const configPath = path.join(root, '.jscpd.json');
  fs.unlinkSync(configPath);
  assert.equal(checkDuplicates(root), 2);
  fs.writeFileSync(configPath, '{invalid');
  assert.equal(checkDuplicates(root), 2);
});

test('changed selection, threshold, reporter or suppression fails closed', (context) => {
  const root = fixture(context);
  for (const change of [
    { threshold: 5 }, { path: ['builder'] }, { ignore: ['**/*'] },
    { reporters: ['console'] }, { mode: 'strict' }, { minTokens: 500 },
  ]) {
    fs.writeFileSync(path.join(root, '.jscpd.json'), JSON.stringify({ ...CONFIG, ...change }));
    assert.equal(checkDuplicates(root), 2);
  }
});

test('missing directory, oversized source and ignore markers fail closed', (context) => {
  const root = fixture(context);
  const sourcePath = path.join(root, 'builder', 'original.py');
  for (const content of ['# jscpd:ignore-start\n' + SOURCE, '\n'.repeat(100001), 'a'.repeat(5242881)]) {
    fs.writeFileSync(sourcePath, content);
    assert.equal(checkDuplicates(root), 2);
  }
  fs.writeFileSync(sourcePath, SOURCE);
  fs.rmdirSync(path.join(root, 'scripts'));
  assert.equal(checkDuplicates(root), 2);
});

test('secondary package configuration cannot hide blocks without changing file selection', (context) => {
  const root = fixture(context);
  for (const settings of [{ ignorePattern: ['.*'] }, { skipComments: true }, null]) {
    fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({ jscpd: settings }));
    let invoked = false;
    assert.equal(checkDuplicates(root, () => {
      invoked = true;
      return { status: 0 };
    }), 2);
    assert.equal(invoked, false);
  }
});

test('empty source population fails instead of reporting a clean scan', (context) => {
  const root = fixture(context);
  fs.unlinkSync(path.join(root, 'builder', 'original.py'));
  assert.equal(checkDuplicates(root), 2);
});

test('tool errors, absent/stale/invalid reports never turn into a pass', (context) => {
  const root = fixture(context);
  const reportPath = path.join(root, CONFIG.output, 'jscpd-report.json');
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  for (const outcome of [
    { status: 0 }, { status: 1 }, { status: null, error: new Error('missing tool') },
  ]) {
    fs.writeFileSync(reportPath, JSON.stringify(report(200, 0)));
    assert.equal(checkDuplicates(root, () => outcome), 2);
    assert.equal(fs.existsSync(reportPath), false);
  }
  assert.equal(checkDuplicates(root, () => {
    fs.writeFileSync(reportPath, '{bad report');
    return { status: 0 };
  }), 2);
  assert.equal(checkDuplicates(root, () => {
    fs.writeFileSync(reportPath, JSON.stringify(report(200, 0)));
    return { status: 7 };
  }), 2);
});

test('canonical command and aggregate propagate failures without suppressions', () => {
  const manifest = require('../package.json');
  assert.equal(manifest.scripts['check:duplicates'], 'node scripts/check_duplicates.cjs');
  const makefile = fs.readFileSync(path.join(ROOT, 'Makefile'), 'utf8');
  assert.match(makefile, /^quality: quality-checks\b/m);
  assert.match(makefile, /^quality-checks:.*\bduplication\b/m);
  assert.match(makefile, /^duplication:\n\tnpm run check:duplicates/m);
  const workflow = fs.readFileSync(path.join(ROOT, '.github/workflows/check.yml'), 'utf8');
  assert.match(workflow, /name: Duplicate code/);
  assert.match(workflow, /node-version: "22"/);
  assert.match(workflow, /npm ci --ignore-scripts/);
  assert.match(workflow, /if: always\(\)[\s\S]*reports\/duplication\//);
  assert.doesNotMatch(workflow, /continue-on-error/);
});

test('CLI exits nonzero on an invalid root rather than claiming success', (context) => {
  const root = fixture(context);
  fs.unlinkSync(path.join(root, '.jscpd.json'));
  const result = spawnSync(process.execPath, [path.join(ROOT, 'scripts/check_duplicates.cjs')], {
    cwd: root, encoding: 'utf8',
  });
  assert.equal(result.status, 2);
  assert.match(result.stderr, /duplication.*error/i);
});
