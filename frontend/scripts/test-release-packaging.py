import importlib.util,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('pack',Path(__file__).with_name('package-release.py'));pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
class Boundary(unittest.TestCase):
 def test_trace_business_directory_survives(self):
  import shutil
  with tempfile.TemporaryDirectory() as t:
   source=Path(t)/'.next';(source/'server/app/trace').mkdir(parents=True);(source/'server/app/trace/page.js').write_text('business');(source/'trace').write_text('telemetry');(source/'cache').mkdir();(source/'cache/local').write_text('cache')
   pack.copy_build(source,Path(t)/'copied')
   self.assertTrue((Path(t)/'copied/server/app/trace/page.js').exists());self.assertFalse((Path(t)/'copied/trace').exists());self.assertFalse((Path(t)/'copied/cache').exists())
 def test_safe_allowlist(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/next(iter(pack.PUBLIC_FILES));p.parent.mkdir(parents=True);p.write_text('{}');self.assertEqual(len(pack.check_public(Path(t),{b'SURF-HELD'})),1)
 def test_old_corpus(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'data/public_surface_mock_v0.json';p.parent.mkdir();p.write_text('{}')
   with self.assertRaises(ValueError):pack.check_public(Path(t),{b'SURF-HELD'})
 def test_leaked_chunk(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'_next/static/chunks/old.js';p.parent.mkdir(parents=True);p.write_text('"SURF-HELD"')
   with self.assertRaises(ValueError):pack.check_public(Path(t),{b'SURF-HELD'})
 def test_secret_file(self):
  with tempfile.TemporaryDirectory() as t:
   (Path(t)/'.env.local').write_text('FAKE_ONLY')
   with self.assertRaises(ValueError):pack.check_public(Path(t),{b'SURF-HELD'})
 def test_link(self):
  with tempfile.TemporaryDirectory() as t:
   (Path(t)/'linked').symlink_to('/tmp')
   with self.assertRaises(ValueError):pack.check_public(Path(t),{b'SURF-HELD'})
if __name__=='__main__':unittest.main()
