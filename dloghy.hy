
(setv -builtin-map map)
(defn map [f l] (list (-builtin-map f l)))

(setv -builtin-print print)
(defn print [&rest args]
  (-builtin-print (unpack-iterable (lfor arg args (if (isinstance arg str) arg (hy-repr arg))))))

(eval-and-compile
  (import hy)
  (import [hy.contrib.hy-repr [hy-repr hy-repr-register]])

  (defn concat [l]
    (setv r [])
    (for [item l] (+= r item))
    r)

  (defclass Tagged []
    (defn __init__ [self name args kwargs]
      (assert (isinstance name hy.HySymbol))
      (setv self.name name)
      (setv self.args args)
      (setv self.kwargs kwargs))

    (defn __getitem__ [self i]
      (if (isinstance i hy.HyKeyword)
        (get self.kwargs i.name)
        (get self.args i)))

    (defn __repr__ [self]
      (.format "({})"
        (.join " "
          (+
            [(+ "`" self.name)]
            (lfor a self.args (hy-repr a))
            (concat (lfor [k v] (.items self.kwargs) [(+ ":" k) (hy-repr v)])))))))

  (defn create-tagged [name &rest args &kwargs kwargs]
    (Tagged name args kwargs))

  (setv hy.HySymbol.__call__ create-tagged)

  (defn -match-case-tagged [value-var code]
    (setv tagged
      (eval
        `(create-tagged
           ~(get code 0)
           ~(unpack-iterable
              (lfor item (cut code 1) (if (isinstance item hy.HyKeyword) item `(quote ~item)))))))

    (setv code-for-args
      (lfor [i code-for-child] (enumerate tagged.args)
        (-match-case `(get (. ~value-var args) ~i) code-for-child)))

    (setv code-for-kwargs
      (lfor [name code-for-child] (.items tagged.kwargs)
        (do
          (setv [code-cond code-action]
            (-match-case `(get (. ~value-var kwargs) ~name) code-for-child))
          [
            `(and (in ~name (. ~value-var kwargs))
               ~code-cond)
            code-action])))

    (setv code-for-children (+ code-for-args code-for-kwargs))

    [
      `(and
         (= (. ~value-var name) ~(str (. tagged name)))
         (= (len (. ~value-var args)) ~(len tagged.args))
         (= (len (. ~value-var kwargs)) ~(len tagged.kwargs))
         ~(unpack-iterable (lfor [code-cond _] code-for-children code-cond)))
      `(do ~(unpack-iterable (lfor [_ code-action] code-for-children code-action)))])

  (defn -match-case-list [value-var code]
    ;; TODO: support &rest
    (setv code-for-children (lfor [i code-for-child] (enumerate code) (-match-case `(get ~value-var ~i) code-for-child)))
    [
      `(and
         (isinstance ~value-var (, list tuple))
         (= (len ~value-var) ~(len code))
         ~(unpack-iterable (lfor [child-cond _] code-for-children child-cond)))
      `(do ~(unpack-iterable (lfor [_ child-cond] code-for-children child-cond)))])

  (defn -match-case [value-var code]
    (cond
      [(isinstance code hy.HySymbol) [True `(setv ~code ~value-var)]] ; should be [let] not [setv] or match should be enclosed in closure
      [(isinstance code hy.HyExpression)
        (setv name (get code 0))
        (cond
          [(and
             (isinstance name hy.HyExpression)
             (= (get name 0) 'quasiquote))
            (-match-case-tagged value-var code)]
          [True (raise (SyntaxError (.format "unknown pattern {0}" (hy-repr code))))])]
      [(isinstance code hy.HyList)
        (-match-case-list value-var code)]
      [True (raise (SyntaxError (.format "unknown pattern {0}" (hy-repr code))))])))

(defmacro match [expr &rest branches]
  (setv value-var (gensym "value"))
  `(do
     (setv ~value-var ~expr)
     (cond
       ~(unpack-iterable
          (lfor branch branches
            (do
              (unless (and (isinstance branch hy.HyList) (= (len branch) 2))
                (raise (SyntaxError (.format "{0} invalid branch syntax" (hy-repr branch)))))
              (setv [code body] branch)
              (setv [code-cond code-action] (-match-case value-var code))
              [code-cond `(do ~code-action ~body)]))))))

(match (`Foo :x 1)
  [(`Foo :x x) x])
