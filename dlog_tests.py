import unittest
import dlog

class SimpleTests(unittest.TestCase):
    def test_projection(self):
        foo = dlog.DataRelation(arity=2)
        foo.add((1, 2))
        foo.add((1, 3))

        foo_p = dlog.SimpleProjection(foo, (1, 0))
        dlog.sync(); self.assertEqual(foo_p.to_set(), { (2, 1), (3, 1) })

        foo.add((2, 4))
        dlog.sync(); self.assertEqual(foo_p.to_set(), { (2, 1), (3, 1), (4, 2) })

    def test_join(self):
        foo = dlog.DataRelation(arity=2)
        foo.add((1, 201))
        foo.add((2, 202))

        bar = dlog.DataRelation(arity=2)
        bar.add((1, 101))
        bar.add((2, 102))

        foo_p = dlog.SimpleJoin(foo, bar, join_k=1)
        dlog.sync(); self.assertEqual(foo_p.to_set(), { (2, 202, 102), (1, 201, 101) })

        foo.add((3, 203))
        dlog.sync(); self.assertEqual(foo_p.to_set(), { (2, 202, 102), (1, 201, 101) })

        bar.add((3, 103))
        dlog.sync(); self.assertEqual(foo_p.to_set(), { (2, 202, 102), (1, 201, 101), (3, 203, 103) })

    def test_external_function(self):
        foo = dlog.DataRelation(arity=2)
        foo.add((1, 10, None))
        foo.add((2, 20, None))

        res = dlog.SimpleExternalFunction(f=(lambda a, b: a+b), a=foo, has_value=False, f_arity=2)
        dlog.sync(); self.assertEqual(res.to_set(), { (1, 10, 11), (2, 20, 22) })

        foo = dlog.DataRelation(arity=2)
        foo.add((1, 10, 11))
        foo.add((2, 20, 22))
        foo.add((2, 20, 23))
        foo.add((3, 30, 23))

        res = dlog.SimpleExternalFunction(f=(lambda a, b: a+b), a=foo, has_value=True, f_arity=2)
        dlog.sync(); self.assertEqual(res.to_set(), { (1, 10, 11), (2, 20, 22) })

    def test_simple_arbitrary_join(self):
        foo = dlog.DataRelation(arity=2)
        foo.add((1, 101))
        foo.add((2, 102))

        bar = dlog.DataRelation(arity=2)
        bar.add((101, 201))
        bar.add((102, 202))

        foo_p = dlog.simple_arbitrary_join(foo, bar, [
            (0, None), (1, 0), (None, 1)
        ])
        dlog.sync(); self.assertEqual(foo_p.to_set(), { (1, 101, 201), (2, 102, 202) })

    def test_masked_intersect_prefix(self):
        pref = dlog.DataRelation(arity=2)
        pref.add((1, 2))
        pref.add((1, 3))

        rel1 = dlog.DataRelation(arity=3)
        rel1.add((2, 2, 3))
        rel1.add((1, 2, 3))

        rel2 = dlog.DataRelation(arity=3)
        rel2.add((1, None, 5))
        rel2.add((2, None, 7))

        r = dlog._masked_intersect_prefix(pref, [
            ((1,1,1), rel1),
            ((1,0,1), rel2),
        ])
        dlog.sync(); self.assertEqual({ k:v.to_set() for k, v in r } , {
            (1, 1, 1): { (1, 2, 3), (1, 2, 5), (1, 3, 5) }
        })

        rel3 = dlog.DataRelation(arity=3)
        rel3.add((1, None, None))

        r = dlog._masked_intersect_prefix(pref, [
            ((1,1,1), rel1),
            ((1,0,1), rel2),
            ((1,0,0), rel3),
        ])
        dlog.sync(); self.assertEqual({ k:v.to_set() for k, v in r } , {
            (1, 1, 1): { (1, 2, 3), (1, 2, 5), (1, 3, 5) },
            (1, 1, 0): { (1, 2, None), (1, 3, None) },
        })

    def test_closure(self):
        edges = dlog.DataRelation(arity=2)
        edges.add((1, 2))
        edges.add((3, 4))

        edges_t = dlog.SimpleProjection(edges, (1, 0))

        transitive_closure = dlog.SimpleLink(arity=2)

        transitive = dlog.SimpleProjection(dlog.SimpleJoin(transitive_closure, edges_t, join_k=1), (2, 1))

        transitive_closure.link(dlog.SimpleUnion([
            transitive,
            edges
        ]))
        dlog.sync(); self.assertEqual(transitive_closure.to_set(), edges.to_set())
        edges.add((2, 3))
        dlog.sync(); self.assertEqual(transitive_closure.to_set(), edges.to_set() | { (1,3), (1, 4), (2, 4) })
        edges.remove((2, 3))

        dlog.sync(); self.assertEqual(transitive_closure.to_set(), edges.to_set())

class OnDemandTests(unittest.TestCase):
    def test_join_data(self):
        foo = dlog.DataRelation(arity=2)
        foo.add((1, 201))
        foo.add((2, 202))
        foo.add((4, 402))

        bar = dlog.DataRelation(arity=2)
        bar.add((1, 101))
        bar.add((2, 102))
        bar.add((3, 302))

        foo_p = dlog.Join(dlog.NotSimple(foo), dlog.NotSimple(bar), join_k=1)
        foo_s = foo_p.filter([
            ((0, 0, 0), dlog.single((None, None, None)))
        ])

        dlog.sync(); self.assertEqual(foo_s.to_set(), { (2, 202, 102), (1, 201, 101) })

        foo.add((3, 203))
        dlog.sync(); self.assertEqual(foo_s.to_set(), { (2, 202, 102), (1, 201, 101), (3, 203, 302) })

        bar.add((3, 103))
        dlog.sync(); self.assertEqual(foo_s.to_set(), { (2, 202, 102), (1, 201, 101), (3, 203, 103), (3, 203, 302) })

    def test_external_function(self):
        foo = dlog.DataRelation(arity=2)
        foo.add((1, 10, None))
        foo.add((2, 20, None))

        res = dlog.ExternalFunction(func=(lambda a, b: a+b), f_arity=2)
        res_f = res.filter([ ((1,1,0), foo) ])
        dlog.sync(); self.assertEqual(res_f.to_set(), { (1, 10, 11), (2, 20, 22) })

        foo = dlog.DataRelation(arity=2)
        foo.add((1, 10, 11))
        foo.add((2, 20, 22))
        foo.add((2, 20, 23))
        foo.add((3, 30, 23))

        res_f = res.filter([ ((1,1,1), foo) ])
        dlog.sync(); self.assertEqual(res_f.to_set(), { (1, 10, 11), (2, 20, 22) })

if __name__ == '__main__':
    unittest.main()
