(import unittest)
(import [hy.contrib.hy-repr [hy-repr hy-repr-register]])
(require [dloghy [*]])
(import [dloghy [*]])

(defclass MatchTests [unittest.TestCase]
  (defn test_simple [self]
    (self.assertEqual (match 1 [x x]) 1)
    (self.assertEqual (match 1 [x (+ x 2)]) 3)
    (self.assertEqual (match 1 [x (+ x 2)] [z z]) 3)
    (self.assertEqual (match 1) None))

  (defn test_list [self]
    (self.assertEqual
      (match [1 2 3]
        [[x] "ONE"]
        [[x y z] (+ x y z)]
        [a "FALLBACK"]) 6)
    (self.assertEqual
      (match [1]
        [[x] "ONE"]
        [[x y z] (+ x y z)]
        [a "FALLBACK"]) "ONE")
    (self.assertEqual
      (match [1 2 3 4]
        [[x] "ONE"]
        [[x y z] (+ x y z)]
        [a a]) [1 2 3 4])
    (self.assertEqual
      (match 1
        [[x] "ONE"]
        [a "TWO"]) "TWO")

    (self.assertEqual
      (match [[1 2] 3]
        [[[x y] z] [x y z]]) [1 2 3]))

  (defn test_tagged [self]
    (self.assertEqual (:x (`Foo :x 1 :y 2)) 1)

    (self.assertEqual
      (match (`Foo :x 1)
        [(`Foo :x x) x])
      1)

    (self.assertEqual
      (match (`Foo :x 1 :y 2)
        [(`Foo :x x) x])
      None)

    (self.assertEqual
      (match (`Foo :z 1)
        [(`Foo :x x) x])
      None)

    (self.assertEqual
      (match (`Bar :x 1)
        [(`Foo :x x) x])
      None)
    ))

(if (= __name__ "__main__")
  (unittest.main))
