import unittest
import dlog

class SimpleTests(unittest.TestCase):
    def test_projection(self):
        foo = dlog.DataRelation(arity=2)
        foo.add((1, 2))
        foo.add((1, 3))

        foo_p = dlog.SimpleProjection(foo, (1, 0))
        self.assertEqual(foo_p.to_set(), { (2, 1), (3, 1) })

        foo.add((2, 4))
        self.assertEqual(foo_p.to_set(), { (2, 1), (3, 1), (4, 2) })

    def test_join(self):
        foo = dlog.DataRelation(arity=2)
        foo.add((1, 201))
        foo.add((2, 202))

        bar = dlog.DataRelation(arity=2)
        bar.add((1, 101))
        bar.add((2, 102))

        foo_p = dlog.SimpleJoin(foo, bar, join_k=1)
        self.assertEqual(foo_p.to_set(), { (2, 202, 102), (1, 201, 101) })

        foo.add((3, 203))
        self.assertEqual(foo_p.to_set(), { (2, 202, 102), (1, 201, 101) })

        bar.add((3, 103))
        self.assertEqual(foo_p.to_set(), { (2, 202, 102), (1, 201, 101), (3, 203, 103) })

if __name__ == '__main__':
    unittest.main()
