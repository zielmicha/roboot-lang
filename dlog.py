import collections, dataclasses, functools
from typing import Any
from dlog_common import *

_action_queue = collections.deque()

def run_later(f, *args):
    _action_queue.append(functools.partial(f, *args))

def sync():
    while _action_queue:
        f = _action_queue.popleft()
        f()

class SimpleRelation:
    def __init__(self):
        self._add_callbacks = []
        self._remove_callbacks = []

        self._tuples = set()
        self._changed = False

        self._debug = False
        self._enable()

    def _enable(self):
        pass

    def _self_add(self, x):
        if x not in self._tuples:
            if self._debug: print('add', self, x)
            self._changed = True
            self._tuples.add(x)
            for cb in self._add_callbacks:
                run_later(cb, x)

    def _self_remove(self, x):
        if x in self._tuples:
            self._changed = True
            self._tuples.remove(x)
            for cb in self._remove_callbacks:
                run_later(cb, x)

    def iter(self): # TODO
        yield from sorted(self._tuples)

    def to_set(self):
        return set(self._tuples)

    def iter_with_prefix(self, prefix): # TODO
        for t in self.iter():
            if t[:len(prefix)] == prefix:
                yield t

    def contains(self, t):
        return t in self._tuples

    def run_for_all(self, f):
        for t in list(self._tuples):
            f(t)

class DataRelation(SimpleRelation):
    def __init__(self, arity):
        self.arity = arity
        super().__init__()

    def add(self, x):
        self._self_add(x)

    def remove(self, x):
        self._self_remove(x)

def single(t):
    d = DataRelation(len(t))
    d.add(t)
    return d

def join_lists(a, b, join_k):
    A = collections.defaultdict(list)

    for t in a:
        A[t[:join_k]].append(t)

    for t1 in b:
        for t2 in A.get(t[:join_k], []):
            yield t1 + t2[join_k:]

class SimpleJoin(SimpleRelation):
    def __init__(self, a, b, join_k):
        self.a = a
        self.b = b
        self.join_k = join_k
        self.arity = self.a.arity + self.b.arity - self.join_k

        super().__init__()

    def _enable(self):
        self.a._add_callbacks.append(self.__a_added)
        self.a._remove_callbacks.append(self.__a_removed)

        self.b._add_callbacks.append(self.__b_added)
        self.b._remove_callbacks.append(self.__b_removed)

        self.b.run_for_all(self.__b_added)
        self.a.run_for_all(self.__a_added)

    def __a_added(self, t):
        for t1 in self.b.iter_with_prefix(t[:self.join_k]):
            self._self_add(t + t1[self.join_k:])

    def __a_removed(self, t):
        for t1 in self.b.iter_with_prefix(t[:self.join_k]):
            self.__remove_tuple_if_needed(t + t1[self.join_k:])

    def __b_added(self, t):
        for t1 in self.a.iter_with_prefix(t[:self.join_k]):
            self._self_add(t1 + t[self.join_k:])

    def __b_removed(self, t):
        for t1 in self.a.iter_with_prefix(t[:self.join_k]):
            self.__remove_tuple_if_needed(t1 + t[self.join_k:])

    def __remove_tuple_if_needed(self, t):
        if t in self._tuples and not self.__contains(t):
            self._self_remove(t)

    def __contains(self, t):
        t1 = t[:self.a.arity]
        t2 = t[:self.join_k] + t[self.a.arity:]
        return self.a.contains(t1) and self.b.contains(t2)

    def get_origins(self, t):
        return [ [ (self.a, t[self.a.arity]), (self.b, t[:self.join_k] + t[self.a.arity:]) ] ]

def project(t, new_axes):
    r = []
    for i in new_axes:
        r.append(t[i])
    return tuple(r)

def unproject(t, new_axes):
    r = []
    for i in new_axes:
        r.append(t[i])
    return tuple(r)

class SimpleProjection(SimpleRelation):
    def __init__(self, a, new_axes):
        self.a = a
        self.new_axes = new_axes
        self.arity = len(new_axes)

        super().__init__()

    def _enable(self):
        self.a._add_callbacks.append(self.__added)
        self.a._remove_callbacks.append(self.__removed)
        self.a.run_for_all(self.__added)

    def __added(self, t):
        self._self_add(project(t, self.new_axes))

    def __removed(self, t):
        self._self_remove(project(t, self.new_axes))

    # def get_origins(self, t):
    #     pass # ???

class SimpleUnion(SimpleRelation):
    def __init__(self, rels=None, *, arity=None):
        assert rels or arity is not None
        self.arity = arity if arity is not None else rels[0].arity
        self.rels = list(rels or [])
        for r in rels: assert r.arity == self.arity

        self.counts = collections.defaultdict(int)
        super().__init__()

    def _enable(self):
        for r in self.rels:
            r._add_callbacks.append(self.__added)
            r._remove_callbacks.append(self.__removed)

        for r in self.rels:
            r.run_for_all(self.__added)

    def __added(self, t):
        self.counts[t] += 1
        self._self_add(t)

    def __removed(self, t):
        self.counts[t] -= 1
        if self.counts[t] == 0:
            del self.counts[t]
            self._self_remove(t)

    @genlist
    def get_origins(self, t):
        for r in rels:
            if r.contains(r):
                yield (r, t)

class SimpleLink(SimpleRelation):
    def __init__(self, arity):
        self.arity = arity
        self.a = None

        super().__init__()

    def _enable(self):
        # FIXME: enable logic
        pass

    def link(self, a):
        self.a = a
        self.a._add_callbacks.append(self.__added)
        self.a._remove_callbacks.append(self.__removed)
        self.a.run_for_all(self.__added)

    def __added(self, t):
        self._self_add(t)

    def __removed(self, t):
        self._self_remove(t)

    def get_origins(self, t):
        if self.a is None:
            return []
        else:
            return self.a.get_origins(t)

def _unproject(t, axes):
    res = []
    for i in axes:
        if i is None:
            res.append(())
        else:
            res.append((t[i], ))
    return tuple(res)


class SimpleExternalFunction(SimpleRelation):
    def __init__(self, *, a, has_value, f, f_arity):
        self.a = a
        self.f = f
        self._has_value = has_value
        self.f_arity = f_arity
        self.arity = f_arity + 1

        self._values = {}

        super().__init__()

    def _enable(self):
        self.a._add_callbacks.append(self.__added)
        self.a._remove_callbacks.append(self.__removed)
        self.a.run_for_all(self.__added)

    def __added(self, t):
        key = t[:self.f_arity]
        value = self.f(*key)
        if not self._has_value or t[-1] == value:
            self._values[key] = value
            self._self_add((*key, value))

    def __removed(self, t):
        if self._has_value:
            self._self_remove(t)
        else:
            key = t[:self.f_arity]
            self._self_remove((*key, self._values[key]))
            del self._values[key]

class Relation:
    def __init__(self):
        self._magic_sets = {}

        super().__init__()

    def __add_magic_set(self, mask, mask_magic_set):
        pass

    def filter(self, a):
        result = self.masked_filter(a)
        bad_resp = [ masked_a for mask, masked_a in result if not all(mask) ]
        if bad_resp:
            raise Exception('uninstantiated response %s' % bad_resp)

        return result[0][1]
    
def reduce_masked(a):
    by_mask = collections.defaultdict(list)
    for mask, a_masked in a: by_mask[mask].append(a_masked)

    return [
        (mask, (lst[0] if len(lst) == 1 else SimpleUnion(lst)))
        for mask, lst in by_mask.items()
    ]

def masked_projection(a, new_axes):
    result = []
    for mask, a_masked in a:
        result.append((
            tuple( mask[a] for a in new_axes ),
            SimpleProjection(a_masked, new_axes),
        ))

    return reduce_masked(result)

def simple_arbitrary_join(r_a, r_b, axes):
    assert isinstance(r_a, SimpleRelation)
    assert isinstance(r_b, SimpleRelation)
    join_on = [ (a, b) for a, b in axes if a is not None and b is not None ]
    join_on_a = [ a for a, b in join_on ]
    join_on_b = [ b for a, b in join_on ]
    join = SimpleJoin(
        SimpleProjection(r_a, tuple(join_on_a) + tuple(range(r_a.arity))),
        SimpleProjection(r_b, tuple(join_on_b) + tuple(range(r_b.arity))),
        len(join_on)
    )
    return SimpleProjection(join, [ (a + len(join_on)) if a is not None else (b + len(join_on) + r_a.arity) for a, b in axes ])

def _masked_intersect_prefix(prefix, a):
    result = []
    for mask, a_masked in a:
        r_mask = tuple([ 1 for i in range(prefix.arity) ]) + mask[prefix.arity:]
        r_masked = simple_arbitrary_join(prefix, a_masked, [
            (i, i) if mask[i] else (i, None)
            for i in range(prefix.arity)
        ] + [
            (None, i)
            for i in range(prefix.arity, a_masked.arity)
        ])
        result.append((r_mask, r_masked))

    return reduce_masked(result)

class NotSimple(Relation):
    def __init__(self, a):
        self.a = a
        self.arity = a.arity

        super().__init__()

    def masked_filter(self, f):
        result = []
        for mask, a_masked in f:
            joined = simple_arbitrary_join(
                self.a, a_masked,
                [ (i, i if mask[i] else None) for i in range(self.arity) ]
            )
            result.append([
                (1,) * self.arity,
                joined
            ])

        return reduce_masked(result)

def _masked_join(a, b, join_k):
    result = []
    for mask, b_masked in b:
        joined = simple_arbitrary_join(
            a, b_masked,
            [ (i, i if mask[i] else None) for i in range(join_k) ]
            + [ (i, None) for i in range(join_k, a.arity) ]
            + [ (None, i) for i in range(join_k, b_masked.arity) ]
        )
        result.append((
            (1,) * a.arity +  mask[join_k:],
            joined
        ))

    return reduce_masked(result)

class Join(Relation):
    def __init__(self, a, b, join_k):
        self.a = a
        self.b = b
        self.join_k = join_k
        self.arity = self.a.arity + self.b.arity - self.join_k

        super().__init__()

    def masked_filter(self, f):
        a_filtered = self.a.filter(masked_projection(f, tuple(range(self.a.arity))))

        m_prefix = SimpleProjection(a_filtered, tuple(range(0, self.join_k)))
        m = masked_projection(f, tuple(range(0, self.join_k)) + tuple(range(self.a.arity, self.arity)))

        b_filtered = self.b.masked_filter(_masked_intersect_prefix(m_prefix, m))
        return _masked_join(a_filtered, b_filtered, self.join_k)

class Projection(Relation):
    def __init__(self, a, new_axes):
        self.a = a
        self.new_axes = new_axes
        self.arity = len(new_axes)

        super().__init__()

    def masked_filter(self, f):
        return masked_projection(
            self.a.masked_filter(f), self.new_axes)

class ExternalFunction(Relation):
    def __init__(self, func, f_arity):
        self.func = func
        self.f_arity = f_arity
        self.arity = f_arity + 1

        super().__init__()

    def masked_filter(self, f):
        result = []

        for mask, f_masked in f:
            assert len(mask) == self.arity

            if not all(mask[:self.f_arity]):
                result.append(((0,) * self.arity, DataRelation(arity=self.arity)))
            else:
                has_value = mask[-1] == 1
                result.append(((1,) * self.arity, SimpleExternalFunction(
                    a=f_masked, f=self.func,
                    f_arity=self.f_arity, has_value=has_value)))

        return reduce_masked(result)

class SimpleEq(SimpleRelation):
    def __init__(self):
        self.arity = 2

        super().__init__()

    def _enable(self):
        self.a._add_callbacks.append(self.__added)
        self.a._remove_callbacks.append(self.__removed)
        self.a.run_for_all(self.__added)

    def __added(self, t):
        if t[0] == t[1]:
            self._self_add(t)

    def __removed(self, t):
        if t[0] == t[1]:
            self._self_remove(t)

class Eq(Relation):
    def __init__(self):
        self.arity = 2

        super().__init__()

    def masked_filter(self, f):
        result = []

        for mask, f_masked in f:
            if mask == (0, 0):
                # is this correct?
                result.append(((0, 0), DataRelation(arity=2)))
            elif mask == (1, 0):
                result.append(((1, 1), SimpleProjection(f_masked, (0, 0))))
            elif mask == (0, 1):
                result.append(((1, 1), SimpleProjection(f_masked, (1, 1))))
            elif mask == (1, 1):
                result.append(((1, 1), SimpleEq()))
            else: assert 0

        return reduce_masked(result)
