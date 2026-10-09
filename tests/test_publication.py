# SPDX-License-Identifier: MIT
"""Non-GL repository/data regression checks. Never imports the rendering fixture."""
import ast
import hashlib
import json
from pathlib import Path
import re
import unittest
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text())

class PublicationChecks(unittest.TestCase):
    def test_findings_schema_and_links(self):
        schema=load('schema/findings.schema.json')
        Draft202012Validator.check_schema(schema)
        data=load('findings.json');Draft202012Validator(schema).validate(data)
        ids=[f['id'] for f in data['findings']]
        self.assertEqual(len(ids),len(set(ids)))
        for f in data['findings']:
            for path in f['evidence']:
                self.assertFalse(Path(path).is_absolute())
                self.assertNotIn('..',Path(path).parts)
                self.assertTrue((ROOT/path).is_file(),path)
        candidate=next(f for f in data['findings'] if f['id']=='SVGA-CLR-HYP-001')
        self.assertEqual(candidate['status'],'untested-hypothesis')

    def test_allowlist_hashes_and_json(self):
        manifest=load('artifact-manifest.json')
        expected={r['path'] for r in manifest['files']}|{'artifact-manifest.json'}
        actual={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts}
        self.assertEqual(actual,expected)
        for row in manifest['files']:
            p=ROOT/row['path'];self.assertFalse(p.is_symlink())
            data=p.read_bytes()
            self.assertEqual(len(data),row['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
            if p.suffix=='.json':json.loads(data)
        for p in ROOT.rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((p.parent/link.split('#')[0]).is_file(),str(p)+': '+link)

    def test_baseline_oracle_and_retained_failure(self):
        evidence=load('evidence/vertex-id.json')
        self.assertEqual(len(evidence['baseline']),8)
        for run in evidence['baseline']:
            self.assertEqual(run['cases'],180)
            faulty=run['stage']=='unpatched' and run['renderer_mode']=='svga'
            self.assertEqual(run['passed'],57 if faulty else 180)
            case=run['minimal_case'];self.assertEqual(case['offset'],17);self.assertEqual(case['width'],2)
            expected={tuple(x) for x in case['expected']}
            observed={tuple(x['values']) for x in case['observations']}
            self.assertEqual(case['passed'],observed==expected)
            if faulty:
                self.assertEqual({x[0]-x[1] for x in observed},{17})
            else:self.assertEqual(observed,expected)
            self.assertEqual(sum(g['cases'] for g in run['groups'].values()),180)
        for run in evidence['extended']:
            self.assertEqual(run['cases'],54)
            self.assertLessEqual(run['passed'],54)
            if run['renderer_mode']=='software':self.assertEqual(run['passed'],54)

    def test_clear_oracle_and_coverage(self):
        for run in load('evidence/unsigned-clear.json')['runs']:
            self.assertEqual(run['application_draws'],0)
            self.assertEqual(run['application_shader_compilations'],0)
            self.assertEqual(run['application_program_links'],0)
            self.assertEqual(run['nonzero_gl_errors'],0)
            for phase in run['phases']:
                all_ok=True
                for read in phase['reads']:
                    self.assertEqual(sum(x['pixels'] for x in read['observed']),4096)
                    expected=phase['expected'][read['attachment']]
                    mismatches=sum(x['pixels'] for x in read['observed'] if x['values']!=expected)
                    self.assertEqual(mismatches,read['mismatch_pixels'])
                    all_ok &= mismatches==0
                    self.assertEqual(read['untouched_poison_pixels'],0)
                self.assertEqual(bool(all_ok),phase['passed'])
                if run['renderer_mode']=='software':self.assertTrue(all_ok)
                if run['condition']==37 and 'marker' in phase['name']:self.assertTrue(all_ok)

    def test_indirect_failure_not_hidden(self):
        d=load('evidence/indirect-reduction.json')
        for run in d['runs']:
            self.assertEqual(len(run['cases']),4)
            for case in run['cases']:
                if run['renderer_mode']=='software':self.assertTrue(case['passed'])
                if run['renderer_mode']=='svga' and case['kind']=='indirect' and case['width']==1:
                    self.assertEqual(case['covered_pixels'],0)
                    self.assertFalse(case['passed'])
                if run['renderer_mode']=='svga':self.assertFalse(case['background_clean'])

    def test_fixture_is_guarded_without_importing(self):
        source=(ROOT/'reproducer/vertex_id.py').read_text()
        tree=ast.parse(source)
        self.assertTrue(any(isinstance(n,ast.FunctionDef) and n.name=='run' for n in tree.body))
        self.assertIn('--execute-rendering',source)
        self.assertIn("assert len(cases)==180",source)
        self.assertIn("assert len(cases)==1",source)
        # CDLL loading is inside run; top level contains no ctypes import/call.
        for n in tree.body:
            if isinstance(n,(ast.Import,ast.ImportFrom)):
                self.assertNotIn('ctypes',ast.unparse(n))
        self.assertNotIn('probe_support',source)
        self.assertNotIn('find_library',source)

if __name__=='__main__':unittest.main(verbosity=2)
