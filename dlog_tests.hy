(import unittest)
(import dlog)

(defclass SimpleTests [unittest.TestCase]
  (defn test_projection [self]
    (setv foo (dlog.DataRelation :arity 2))
    (foo.add (, 1 2))
    (foo.add (, 1 3))

    (setv foo_p (dlog.SimpleProjection foo (, 1 0)))
    (dlog.sync) (self.assertEqual (foo_p.to_set) (set [(, 2 1) (, 3 1)] ))

    (foo.add (, 2 4))
    (dlog.sync) (self.assertEqual (foo_p.to_set) (set [(, 2 1) (, 3 1) (, 4 2)] ))))

(if (= __name__ "__main__")
    (unittest.main))
