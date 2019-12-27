import collections, dataclasses
from typing import Any

class TupleSet:
    def __init__(self):
        pass

class Relation:
    def __init__(self):
        self._add_callbacks = []
        self._remove_callbacks = []
        self._step_done_callbacks = []

        self._tuples = set()
        self._changed = False

        self._enable()

    def _enable(self):
        pass

    def _self_add(self, x):
        if x not in self._tuples:
            self._changed = True
            self._tuples.add(x)
            for cb in self._add_callbacks:
                cb(x)

    def _self_remove(self, x):
        self._changed = True
        self._tuples.remove(x)
        for cb in self._remove_callbacks:
            cb(x)

    def _self_step_done(self):
        if self._changed:
            self._changed = False
            for cb in self._step_done_callbacks:
                cb()

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

    def add_to_magic_set(self):
        pass

class DataRelation(Relation):
    def __init__(self, arity):
        self.arity = arity
        super().__init__()

    def add(self, x):
        self._self_add(x)
        self._self_step_done()

    def remove(self, x):
        self._self_remove(x)
        self._self_step_done()

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

class SimpleJoin(Relation):
    def __init__(self, a, b, join_k):
        self.a = a
        self.b = b
        self.join_k = join_k
        self.arity = self.a.arity + self.b.arity - self.join_k

        self._remove_a = set()
        self._remove_b = set()

        super().__init__()

    def _enable(self):
        self.a._add_callbacks.append(self.__a_added)
        self.a._remove_callbacks.append(self.__a_removed)

        self.b._add_callbacks.append(self.__b_added)
        self.b._remove_callbacks.append(self.__b_removed)

        self.a._step_done_callbacks.append(self.__step_done)
        self.b._step_done_callbacks.append(self.__step_done)

        self.b.run_for_all(self.__b_added)
        self.a.run_for_all(self.__a_added)

    def __a_added(self, t):
        if t in self._remove_a:
            self._remove_a.remove(t)

        for t1 in self.b.iter_with_prefix(t[:self.join_k]):
            self._self_add(t + t1[self.join_k:])

    def __a_removed(self, t):
        self._remove_a.add(t)

    def __b_added(self, t):
        if t in self._remove_b:
            self._remove_b.remove(t)

        for t1 in self.a.iter_with_prefix(t[:self.join_k]):
            self._self_add(t1 + t[self.join_k:])

    def __b_removed(self, t):
        self._remove_b.add(t)

    def __step_done(self):
        # TODO: we can do better
        for t in list(self._remove_a):
            for t1 in self.b.iter_with_prefix(t[:self.join_k]):
                self.__remove_tuple_if_needed(t + t1[self.join_k:])

        for t in list(self._remove_b):
            for t1 in self.a.iter_with_prefix(t[:self.join_k]):
                self.__remove_tuple_if_needed(t1 + t[self.join_k:])

        self._self_step_done()

    def __remove_tuple_if_needed(self, t):
        if t in self._tuples and not self.__contains(t):
            self._self_remove(t)

    def __contains(self, t):
        t1 = t[:self.a.arity]
        t2 = t[:self.join_k] + t[self.a.arity:]
        return self.a.contains(t1) and self.b.contains(t2)

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

class SimpleProjection(Relation):
    def __init__(self, a, new_axes):
        self.a = a
        self.new_axes = new_axes
        self.arity = len(new_axes)

        super().__init__()

    def _enable(self):
        self.a._add_callbacks.append(self.__added)
        self.a._remove_callbacks.append(self.__removed)
        self.a._step_done_callbacks.append(self._self_step_done)
        self.a.run_for_all(self.__added)

    def __added(self, t):
        self._self_add(project(t, self.new_axes))

    def __removed(self, t):
        self._self_remove(project(t, self.new_axes))

class SimpleUnion(Relation):
    def __init__(self, a, b):
        self.arity = a.arity
        self.a = a
        self.b = b
        assert self.a.arity == self.b.arity

        super().__init__()

    def _enable(self):
        self.a._add_callbacks.append(self.__added)
        self.a._remove_callbacks.append(self.__removed)
        self.a._step_done_callbacks.append(self._self_step_done)

        self.b._add_callbacks.append(self.__added)
        self.b._remove_callbacks.append(self.__removed)
        self.b._step_done_callbacks.append(self._self_step_done)

        self.b.run_for_all(self.__added)
        self.a.run_for_all(self.__added)

    def __added(self, t):
        self._self_add(t)

    def __removed(self, t):
        if not self.a.contains(t) and not self.b.contains(t):
            self._self_remove(t)

class SimpleLink(Relation):
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
        self.a._step_done_callbacks.append(self._self_step_done)
        self.a.run_for_all(self.__added)
        self._self_step_done()

    def __added(self, t):
        self._self_add(t)

    def __removed(self, t):
        self._self_remove(t)

def _unproject(t, axes):
    res = []
    for i in axes:
        if i is None:
            res.append(())
        else:
            res.append((t[i], ))
    return tuple(res)

class SimpleUnprojection(Relation):
    def __init__(self, a, arity, new_axes):
        self.a = a
        self.old_axes = [None] * arity
        for i, j in enumerate(new_axes): self.old_axes[j] = i
        self.arity = arity

        super().__init__()

    def _enable(self):
        self.a._add_callbacks.append(self.__added)
        self.a._remove_callbacks.append(self.__removed)
        self.a._step_done_callbacks.append(self._self_step_done)
        self.a.run_for_all(self.__added)

    def __added(self, t):
        self._self_add(_unproject(t, self.old_axes))

    def __removed(self, t):
        self._self_remove(_unproject(t, self.old_axes))

class MagicRelation(Relation):
    def __init__(self):
        self._magic_set = DataRelation()
        super().__init__()

    def add_to_magic_set(self, r):
        self._magic_set = SimpleUnion(r, self._magic_set)

class Projection(Relation):
    def __init__(self, a, new_axes):
        self.a = a
        self.new_axes = new_axes
        self.arity = len(new_axes)

        super().__init__()

    def _enable(self):
        self.a._add_callbacks.append(self.__added)
        self.a._remove_callbacks.append(self.__removed)
        self.a._step_done_callbacks.append(self._self_step_done)
        self.a.add_to_magic_set(_unproject_relation(self._magic_set, self.new_axes))

        self.a.run_for_all(self.__added)

    def __added(self, t):
        self._self_add(project(t, self.new_axes))

    def __removed(self, t):
        self._self_remove(project(t, self.new_axes))
