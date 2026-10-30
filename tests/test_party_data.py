"""Offline checks of real retained evidence. Synthetic verdicts test parsing only."""
import copy
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import build as builder
from acquire_party_evidence import OfficialRedirects, acquire, entries, readable
from import_party_evidence import seed
from party_data import candidate_digest, external_reviews, load_json, retained_bytes, validate, validate_files
from party_source_storage import decode_response, encode_response


class PartyContractTests(unittest.TestCase):
    def setUp(self):
        # Keep the original five-source boundary fixtures independent of later
        # extraction. Production proposal records have their own real-data tests.
        self.data, self.manifest = seed(ROOT / 'data/party-evidence/20261030-repair2', include_proposals=False)
        self.blobs = {s[k]: retained_bytes(s[k]) for s in self.manifest['sources'] for k in ('path', 'raw_path')}
        rf = self.source('resolution-comparison-2024')
        original = self.blobs[rf['raw_path']]
        rf['raw_path'] = 'data/party-evidence/synthetic/resolution-comparison-2024-response.json'
        self.blobs[rf['raw_path']] = encode_response(original)
        self.today = date.fromisoformat(max(s['retrieved_at'][:10] for s in self.manifest['sources']))

    @property
    def proposal(self):
        return next(p for p in self.data['parties'] if p['id'] == '15')['proposals'][0]

    def source(self, key):
        return next(s for s in self.manifest['sources'] if s['id'] == key)

    def check(self, **kwargs):
        return validate(self.data, self.manifest, read=self.blobs.__getitem__,
                        as_of=kwargs.pop('as_of', self.today), **kwargs)

    def refused(self, message, **kwargs):
        with self.assertRaisesRegex(ValueError, message):
            self.check(**kwargs)

    def rewrite_roster(self, mutate):
        source = self.source('commons')
        raw = load_json(decode_response(self.blobs[source['raw_path']]))
        mutate(raw)
        encoded = json.dumps(raw, ensure_ascii=False).encode()
        self.blobs[source['path']] = encoded
        self.blobs[source['raw_path']] = encode_response(encoded)
        source['sha256'] = source['raw_sha256'] = hashlib.sha256(encoded).hexdigest()

    def test_actual_retained_roster_and_unreviewed_state(self):
        report = self.check()
        self.assertEqual((report['party_count'], report['mp_count']), (15, 650))
        for field in ('public_accepted', 'review_bindings_complete', 'proposal_coverage_complete'):
            self.assertFalse(report[field])
        actual = validate_files(as_of=self.today)
        for key in ('party_count', 'mp_count', 'public_accepted', 'review_bindings_complete'):
            self.assertEqual(actual[key], report[key])
        self.assertEqual({m['classification']: m['mp_count'] for m in self.data['non_party_members']},
                         {'independent': 11, 'speaker': 1})
        self.refused('reviews pending', require_reviews=True)
        self.refused('proposal coverage incomplete', require_coverage=True)

    def test_actual_import_is_reproducible(self):
        data, manifest = seed(ROOT / Path(self.source('commons')['path']).parent)
        self.assertEqual(data, load_json((ROOT / 'data/parties.json').read_bytes()))
        self.assertEqual(manifest, load_json((ROOT / 'data/party-sources.json').read_bytes()))

    def test_actual_amounts_and_periods(self):
        self.assertEqual(self.proposal['costs_claimed']['items'][0]['amount'], '4835')
        self.assertEqual(self.proposal['funding_claimed']['items'][0]['amount'], '7350')
        snp = next(p for p in self.data['parties'] if p['id'] == '29')['proposals'][0]
        self.assertEqual(snp['costs_claimed']['items'][0]['amount'], '1.6')
        self.assertEqual(snp['costs_claimed']['items'][0]['basis'], 'unspecified')
        self.assertIsNone(snp['fiscal_year'])
        self.assertEqual(snp['funding_claimed']['availability'], 'unavailable')
        self.assertIn('not verification', self.proposal['assessments']['items'][0]['scope'])

    def test_unavailable_fixture_independent_of_committed_candidate(self):
        data = {'schema_version': 1, 'status': 'unavailable', 'as_of': None, 'reason': 'Synthetic only',
                'roster_sources': [], 'parties': [], 'non_party_members': [],
                'reviews': {'fiscal': None, 'editorial': None}}
        manifest = {'schema_version': 1, 'sources': []}
        self.assertEqual(validate(data, manifest, as_of=self.today)['status'], 'unavailable')
        with self.assertRaisesRegex(ValueError, 'roster evidence unavailable'):
            validate(data, manifest, as_of=self.today, require_coverage=True)

    def test_unknown_and_missing_fields(self):
        for obj in (self.data, self.manifest, self.source('commons'), self.data['parties'][0],
                    self.proposal, self.proposal['evidence'], self.proposal['costs_claimed'],
                    self.proposal['costs_claimed']['items'][0], self.proposal['assessments']['items'][0]):
            with self.subTest(keys=list(obj)):
                key = next(iter(obj))
                old = obj.pop(key)
                self.refused('missing or extra')
                obj[key] = old
                obj['unexpected'] = 'private'
                self.refused('missing or extra')
                del obj['unexpected']

    def test_missing_party_independent_and_roster_source(self):
        for mutate, message in (
            (lambda: self.data['parties'].pop(0), 'party coverage incomplete'),
            (lambda: self.data['non_party_members'].pop(), 'independent/Speaker coverage'),
            (lambda: self.data['roster_sources'].clear(), 'one complete dated roster'),
            (lambda: self.manifest['sources'].pop(0), 'missing roster source'),
        ):
            self.setUp()
            mutate()
            self.refused(message)

    def test_rehashed_missing_or_duplicate_roster_group(self):
        self.rewrite_roster(lambda p: p['items'].pop(0))
        self.refused('unrepresented party')
        self.setUp()
        self.rewrite_roster(lambda p: p['items'].append(p['items'][0]))
        self.refused('duplicate Parliament party')

    def test_zero_totalresults_is_not_zero_mps(self):
        page = load_json(self.blobs[self.source('commons')['path']])
        self.assertEqual(page['totalResults'], 0)
        self.assertEqual(self.check()['mp_count'], sum(r['value']['total'] for r in page['items']))
        self.rewrite_roster(lambda p: p['items'][0]['value'].update(total=0))
        self.refused('MP count')

    def test_count_classification_house_date_and_filter(self):
        for mutate, message in (
            (lambda: self.data['parties'][0].update(mp_count=True), 'expected integer'),
            (lambda: self.data['parties'][0].update(mp_count=999), 'MP coverage differs'),
            (lambda: self.rewrite_roster(lambda p: p['items'][0]['value'].update(male=0)), 'reconcile'),
            (lambda: self.rewrite_roster(lambda p: p['items'][0]['value']['party'].update(isIndependentParty=True)), 'unrepresented party'),
            (lambda: self.rewrite_roster(lambda p: p['links'][0].update(href='wrong date/house')), 'self link'),
            (lambda: self.source('commons').update(url=self.source('commons')['url'] + '?PartyId=15'), 'unfiltered dated'),
            (lambda: self.source('commons').update(url=self.source('commons')['url'].replace('/1/', '/2/')), 'unfiltered dated'),
        ):
            self.setUp()
            mutate()
            with self.subTest(message=message):
                self.refused(message)

    def test_party_order_and_duplicates(self):
        self.data['parties'].reverse()
        self.refused('parties must be alphabetical')
        self.setUp()
        self.data['parties'].append(copy.deepcopy(self.data['parties'][0]))
        self.refused('parties: duplicate')

    def test_complete_response_and_text_hashes(self):
        for field, message in (('path', 'changed snapshot hash'), ('raw_path', 'changed original response hash')):
            self.setUp()
            path = self.source('labour-fiscal-2024')[field]
            self.blobs[path] = (encode_response(decode_response(self.blobs[path]) + b' changed')
                                if field == 'raw_path' else self.blobs[path] + b' changed')
            self.refused(message)

    def test_all_five_original_hashes_and_extractions_survive_storage(self):
        self.assertEqual(len(self.manifest['sources']), 5)
        for source in self.manifest['sources']:
            with self.subTest(source=source['id']):
                stored = self.blobs[source['raw_path']]
                original = decode_response(stored)
                self.assertEqual(hashlib.sha256(original).hexdigest(), source['raw_sha256'])
                self.assertEqual(readable(original, source['kind']).encode(), self.blobs[source['path']])
                self.assertEqual(stored, encode_response(original))

    def test_container_corruption_and_rehashed_storage_cannot_hide_original_change(self):
        path = self.source('labour-fiscal-2024')['raw_path']
        self.blobs[path] = self.blobs[path].replace(b'http-response', b'invented-response', 1)
        self.refused('container schema')
        self.setUp()
        path = self.source('labour-fiscal-2024')['raw_path']
        self.blobs[path] = encode_response(decode_response(self.blobs[path]) + b'\r\n ')
        self.refused('changed original response hash')

    def test_import_corruption_preserves_existing_candidate_files(self):
        import import_party_evidence as importer
        import party_data
        from unittest.mock import patch
        import shutil
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            relative = Path(self.source('commons')['path']).parent
            shutil.copytree(ROOT / relative, root / relative)
            for name in ('parties.json', 'party-sources.json'):
                (root / 'data' / name).write_bytes(b'last verified record')
            raw_path = root / self.source('commons')['raw_path']
            raw_path.write_bytes(encode_response(decode_response(raw_path.read_bytes()) + b' '))
            with patch.object(importer, 'ROOT', root), patch.object(party_data, 'ROOT', root), \
                    patch.object(sys, 'argv', ['import_party_evidence.py', '--evidence-dir', str(root / relative)]):
                with self.assertRaises(SystemExit) as failure:
                    importer.main()
            self.assertEqual(failure.exception.code, 1)
            for name in ('parties.json', 'party-sources.json'):
                self.assertEqual((root / 'data' / name).read_bytes(), b'last verified record')

    def test_rehash_cannot_conceal_edited_extraction_or_false_date(self):
        source = self.source('labour-fiscal-2024')
        self.blobs[source['path']] += b' changed'
        source['sha256'] = hashlib.sha256(self.blobs[source['path']]).hexdigest()
        self.refused('complete response extraction')
        self.setUp()
        self.source('labour-fiscal-2024')['published_on'] = '2024-06-12'
        self.refused('publication date differs')

    def test_owner_publisher_kind_and_domains(self):
        for key, field, value, message in (
            ('labour-fiscal-2024', 'party_id', '29', 'publication owner mismatch'),
            ('labour-fiscal-2024', 'url', 'https://labour.org.uk.attacker.invalid/', 'owner/domain'),
            ('resolution-comparison-2024', 'url', 'https://resolutionfoundation.org.attacker.invalid/', 'publisher/domain'),
            ('resolution-comparison-2024', 'publisher', 'Unknown Institute', 'publisher/domain'),
            ('commons', 'url', 'https://members-api.parliament.uk.attacker.invalid/', 'Parliament API'),
        ):
            self.setUp()
            self.source(key)[field] = value
            with self.subTest(field=field):
                self.refused(message)

    def test_quotes_and_offsets(self):
        for field, value in (('quote', 'invented judgement'), ('start', 1), ('end', 9999999)):
            self.setUp()
            self.proposal['evidence'][field] = value
            self.refused('quotation/locator')

    def test_missing_not_zero_decimal_units_and_claim_status(self):
        snp = next(p for p in self.data['parties'] if p['id'] == '29')['proposals'][0]
        snp['funding_claimed']['items'] = [{'amount': '0'}]
        self.refused('missing is not zero')
        for field, value, message in (('amount', 4835, 'decimal string'), ('amount', 'NaN', 'decimal string'),
                                      ('unit', 'EUR', 'unknown claimed unit'), ('basis', 'actual', 'time basis')):
            self.setUp()
            self.proposal['costs_claimed']['items'][0][field] = value
            self.refused(message)
        self.setUp()
        self.proposal['status'] = 'actual'
        self.refused('invalid proposal status')

    def test_duplicate_amount_and_assessment_attribution(self):
        items = self.proposal['costs_claimed']['items']
        items.append(copy.deepcopy(items[0]))
        self.refused('items: duplicate')
        self.setUp()
        self.proposal['assessments']['items'][0]['publisher'] = 'Full Fact'
        self.refused('attribution mismatch')

    def test_false_amount_and_proposal_source_date(self):
        self.proposal['costs_claimed']['items'][0]['amount'] = '0'
        self.refused('amount absent from exact source')
        self.setUp()
        self.proposal['proposal_date'] = '2024-06-12'
        self.refused('source date mismatch')
        self.setUp()
        self.proposal['assessments']['items'][0]['assessed_on'] = '2024-06-12'
        self.refused('assessment date mismatch')

    def test_missing_year_and_source_duplicates(self):
        snp = next(p for p in self.data['parties'] if p['id'] == '29')['proposals'][0]
        snp['fiscal_year_reason'] = None
        self.refused('unavailable fiscal year reason')
        self.setUp()
        self.manifest['sources'].append(copy.deepcopy(self.manifest['sources'][0]))
        self.refused('duplicate source id')

    def test_snapshot_symlink_rejected(self):
        import party_data
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / 'data/party-evidence/test'
            directory.mkdir(parents=True)
            (root / 'real.txt').write_text('private')
            (directory / 'link.txt').symlink_to(root / 'real.txt')
            with patch.object(party_data, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'symlink'):
                    retained_bytes('data/party-evidence/test/link.txt')

    def test_source_coverage_and_paths(self):
        self.proposal['assessments'] = {'availability': 'unavailable', 'reason': 'Synthetic removal', 'items': []}
        self.refused('unused or unreferenced')
        self.setUp()
        self.source('commons')['path'] = 'data/raw/parties/../../private.json'
        self.refused('snapshot path')
        with self.assertRaisesRegex(ValueError, 'party-evidence'):
            retained_bytes('../private.json')

    def test_future_stale_timestamp_and_fiscal_year(self):
        self.refused('future retrieval', as_of=self.today - timedelta(days=1))
        self.refused('stale roster', as_of=self.today + timedelta(days=31))
        self.source('labour-fiscal-2024')['retrieved_at'] = '2026-01-01T00:00:00+00:00'
        self.refused('stale publication')
        self.setUp()
        self.source('labour-fiscal-2024')['retrieved_at'] = '2026-10-30T12:00:00'
        self.refused('must be UTC')
        self.setUp()
        self.proposal['fiscal_year'] = '2028-30'
        self.refused('invalid fiscal year')

    def test_overlap_cannot_hide_in_distinct_groups(self):
        other = copy.deepcopy(self.proposal)
        other.update(id='labour-variant', title='Variant', overlap_key='different-key')
        other['evidence']['start'] += 1
        other['evidence']['quote'] = other['evidence']['quote'][1:]
        next(p for p in self.data['parties'] if p['id'] == '15')['proposals'].append(other)
        self.refused('overlapping proposal excerpts')
        other['overlap_key'] = self.proposal['overlap_key']
        other['overlaps_with'] = [self.proposal['id']]
        self.proposal['overlaps_with'] = [other['id']]
        self.check()
        self.assertNotIn('total_cost', self.check())

    def test_duplicate_excerpt(self):
        other = copy.deepcopy(self.proposal)
        other.update(id='variant', title='Variant')
        next(p for p in self.data['parties'] if p['id'] == '15')['proposals'].append(other)
        self.refused('duplicate proposal excerpt')

    def test_no_in_data_approvals_and_digest_binds_record(self):
        digest = candidate_digest(self.data, self.manifest)
        self.data['reviews']['fiscal'] = {'reviewer': 'Invented'}
        self.refused('in-data approvals prohibited')
        self.data['reviews']['fiscal'] = None
        self.proposal['baseline'] += ' changed'
        self.assertNotEqual(digest, candidate_digest(self.data, self.manifest))

    def test_external_verdicts_exact_binding_and_blockers(self):
        # These parser fixtures are never written as review receipts or evidence.
        binding = {'base_sha': 'a' * 40, 'candidate_sha': 'b' * 40, 'tree': 'c' * 40}
        receipts = {role: {**binding, 'findings': []} for role in ('fiscal', 'editorial')}
        self.assertTrue(external_reviews(receipts, binding))
        receipts['fiscal']['candidate_sha'] = 'd' * 40
        with self.assertRaisesRegex(ValueError, 'exact candidate mismatch'):
            external_reviews(receipts, binding)
        receipts['fiscal']['candidate_sha'] = binding['candidate_sha']
        receipts['fiscal']['findings'] = [{'severity': 'blocking', 'file': 'data/parties.json',
                                           'line': 1, 'issue': 'Synthetic pending coverage'}]
        with self.assertRaisesRegex(ValueError, 'blocking findings'):
            external_reviews(receipts, binding)

    def test_json_duplicate_and_nonfinite_guards(self):
        for raw in ('{"a": 1, "a": 2}', '{"a": NaN}', '{"a": Infinity}'):
            with self.assertRaises(ValueError):
                load_json(raw)

    def test_fiscal_public_allowlist_unchanged(self):
        self.assertEqual(builder.PUBLIC_FILES, {'index.html', 'methods.html', 'icon.svg', 'data/spending.json'})


class AcquisitionTests(unittest.TestCase):
    def fixture_fetch(self, url):
        entry = next(e for e in entries('2026-10-30') if e[4] == url)
        if entry[1] == 'roster':
            return b'{"items":[]}', 200, url, 'application/json'
        return ('<html>\r\n \t<script>ignored</script><p>' + entry[6] + '</p> \t\r\n</html>').encode(), 200, url, 'text/html'

    def test_complete_bytes_text_hash_and_observed_time(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'new'
            self.assertTrue(acquire(target, '2026-10-30', self.fixture_fetch))
            result = load_json((target / 'acquisition.json').read_bytes())
            self.assertEqual(len(result['sources']), 5)
            for source in result['sources']:
                stored = (target / source['raw_path']).read_bytes()
                raw = decode_response(stored)
                self.assertEqual(raw, self.fixture_fetch(source['url'])[0])
                self.assertEqual(stored, encode_response(raw))
                self.assertEqual(hashlib.sha256(raw).hexdigest(), source['raw_sha256'])
                self.assertEqual(readable(raw, source['kind']), (target / source['path']).read_text())
                self.assertIn('+00:00', source['retrieved_at'])

    def test_storage_expansion_counts_against_acquisition_budget(self):
        def expands(url):
            # Raw UTF-8 fits the old limit, but escaped uncompressed storage does not.
            return b'{"text":"' + b'\x7f' * 130000 + b'"}', 200, url, 'application/json'
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'expanded'
            self.assertFalse(acquire(target, '2026-10-30', expands))
            result = load_json((target / 'acquisition.json').read_bytes())
            self.assertFalse(result['outcomes'][0]['retained'])
            self.assertIn('budget', result['outcomes'][0]['error'])
            self.assertFalse((target / 'commons-response.json').exists())

    def test_http_failure_preserved_no_overwrite(self):
        def blocked(url):
            raise HTTPError(url, 403, 'Forbidden', {}, None)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'failed'
            self.assertFalse(acquire(target, '2026-10-30', blocked))
            receipt = load_json((target / 'acquisition.json').read_bytes())
            self.assertEqual(receipt['sources'], [])
            self.assertTrue(all(r['http_status'] == 403 and not r['retained'] for r in receipt['outcomes']))
            before = (target / 'acquisition.json').read_bytes()
            with self.assertRaises(FileExistsError):
                acquire(target, '2026-10-30', self.fixture_fetch)
            self.assertEqual(before, (target / 'acquisition.json').read_bytes())

    def test_wrong_content_type_or_publication_locator(self):
        def corrupt(url):
            raw, status, final, kind = self.fixture_fetch(url)
            return raw.replace(b'datePublished', b'invented'), status, final, 'text/plain'
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'bad'
            self.assertFalse(acquire(target, '2026-10-30', corrupt))
            self.assertEqual(load_json((target / 'acquisition.json').read_bytes())['sources'], [])

    def test_absent_date_locator_and_size_budget_not_silent_success(self):
        def missing_date(url):
            raw, status, final, kind = self.fixture_fetch(url)
            return raw.replace(b'datePublished', b'invented'), status, final, kind
        def oversized(url):
            return b'x' * 750001, 200, url, 'application/json' if 'parliament.uk' in url else 'text/html'
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'bad_date'
            self.assertFalse(acquire(target, '2026-10-30', missing_date))
            result = load_json((target / 'acquisition.json').read_bytes())
            self.assertTrue(any('date locator absent' in r.get('error', '') for r in result['outcomes']))
            target = Path(folder) / 'oversized'
            self.assertFalse(acquire(target, '2026-10-30', oversized))
            self.assertEqual(load_json((target / 'acquisition.json').read_bytes())['sources'], [])

    def test_symlink_and_redirect_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'link'
            target.symlink_to(folder, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                acquire(target / 'new', '2026-10-30', self.fixture_fetch)
        with self.assertRaisesRegex(ValueError, 'official HTTPS origin'):
            OfficialRedirects().redirect_request(Request('https://labour.org.uk/source'), None,
                                                 302, 'redirect', {}, 'https://attacker.invalid/')


class ResponseStorageTests(unittest.TestCase):
    def test_every_byte_and_whitespace_round_trip(self):
        for raw in (b'', bytes(range(256)), b'\r\n \t\r\nno final newline \t', b'\x00\xff\x85\x0b\x0c'):
            with self.subTest(raw=repr(raw)):
                stored = encode_response(raw)
                self.assertEqual(decode_response(stored), raw)
                self.assertTrue(stored.isascii())
                self.assertTrue(all(line == line.rstrip() for line in stored.splitlines()))

    def test_independent_decoder_cli_hash_binding_and_exclusive_output(self):
        import subprocess
        raw = bytes(range(256)) + b'\r\n \t'
        with tempfile.TemporaryDirectory() as folder:
            container, output = Path(folder) / 'response.json', Path(folder) / 'original'
            container.write_bytes(encode_response(raw))
            command = [sys.executable, str(ROOT / 'scripts/party_source_storage.py'), str(container),
                       '--output', str(output), '--sha256']
            refused = subprocess.run(command + ['0' * 64], capture_output=True)
            self.assertEqual(refused.returncode, 1)
            self.assertIn(b'manifest hash', refused.stderr)
            self.assertFalse(output.exists())
            accepted = subprocess.run(command + [hashlib.sha256(raw).hexdigest()], capture_output=True)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertEqual(output.read_bytes(), raw)
            refused = subprocess.run(command + [hashlib.sha256(raw).hexdigest()], capture_output=True)
            self.assertEqual(refused.returncode, 1)
            self.assertEqual(output.read_bytes(), raw)

    def test_corruption_schema_duplicates_and_noncanonical_encoding_refused(self):
        stored = encode_response(b'original \r\n\xff')
        document = json.loads(stored)
        mutations = [
            {**document, 'format': 'unknown'}, {**document, 'byte_length': True},
            {**document, 'byte_length': document['byte_length'] + 1},
            {**document, 'sha256': '0' * 64}, {**document, 'lines': ['edited']},
            {**document, 'lines': [1]}, {**document, 'lines': ['\u20ac']},
            {**document, 'extra': 'ignored'}, {k: v for k, v in document.items() if k != 'sha256'},
        ]
        invalid = [json.dumps(v).encode() for v in mutations]
        invalid += [stored + b' ', stored.replace(b'{', b'{"format":"duplicate",', 1),
                    stored.replace(b'"byte_length": 12', b'"byte_length": NaN'),
                    b'original raw HTML', b'[]', b'null', b'\xff']
        for value in invalid:
            with self.subTest(value=repr(value[:80])):
                with self.assertRaises(ValueError):
                    decode_response(value)


if __name__ == '__main__':
    unittest.main()
