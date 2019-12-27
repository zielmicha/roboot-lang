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

    def test_closure(self):
        edges = dlog.DataRelation(arity=2)
        edges.add((1, 2))
        edges.add((3, 4))

        edges_t = dlog.SimpleProjection(edges, (1, 0))

        transitive_closure = dlog.SimpleLink(arity=2)

        transitive = dlog.SimpleProjection(dlog.SimpleJoin(transitive_closure, edges_t, join_k=1), (2, 1))

        transitive_closure.link(dlog.SimpleUnion(
            transitive,
            edges
        ))
        self.assertEqual(transitive_closure.to_set(), edges.to_set())
        edges.add((2, 3))
        self.assertEqual(transitive_closure.to_set(), edges.to_set() | { (1,3), (1, 4), (2, 4) })
        edges.remove((2, 3))
        self.assertEqual(transitive_closure.to_set(), edges.to_set())

    def test_unprojection(self):
        foo = dlog.DataRelation(arity=2)
        foo.add((1, 2))
        foo.add((1, 3))

        foo_p = dlog.SimpleUnprojection(foo, 3, (1, 0))
        self.assertEqual(foo_p.to_set(), { ((2,), (1,), ()), ((3,), (1,), ()) })

        foo.add((2, 4))
        self.assertEqual(foo_p.to_set(), { ((2,), (1,), ()), ((3,), (1,), ()), ((4,), (2,), ()) })

if __name__ == '__main__':
    unittest.main()
