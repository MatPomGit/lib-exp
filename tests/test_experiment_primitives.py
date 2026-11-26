import unittest, sys, tempfile, hashlib
from pathlib import Path
from itertools import permutations
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from lib_exp import sequence, sequence_count, source_hashes

class ExperimentTests(unittest.TestCase):
    def test_exact_twelve(self):
        c=("ALTERNATING","MATCHED_STEREO","QUIET")
        f=("LEFT","RIGHT")
        self.assertEqual(sequence_count(c,f),12)
        self.assertEqual([sequence(c,f,i) for i in range(12)],[(p,s) for s in f for p in permutations(c)])
    def test_invalid(self):
        for c,f,i in [(("a","a"),("b",),0),((),("b",),0),(("a",),("b",),True),(("a",),("b",),1)]:
            with self.assertRaises(ValueError): sequence(c,f,i)
    def test_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"a").write_bytes(b"abc")
            self.assertEqual(source_hashes(root,["a"]),{"a":hashlib.sha256(b"abc").hexdigest()})
            (root/"link").symlink_to(root/"a")
            for paths in (["../a"],["link"],["a","a"]):
                with self.assertRaises(ValueError): source_hashes(root,paths)
