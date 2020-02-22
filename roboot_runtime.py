
class frozenlist(list):
    def __setitem__(self, i, val):
        _frozen_exc()

    def __delitem__(self, i):
        _frozen_exc()

    def reverse(self):
        _frozen_exc()

    def insert(self, i, x):
        _frozen_exc()

    def append(self, x):
        _frozen_exc()

    def sort(self, *args, **kwargs):
        _frozen_exc()

    def pop(self, i=None):
        _frozen_exc()

    def remove(self, x):
        _frozen_exc()

    def extend(self, l):
        _frozen_exc()

    def __iadd__(self, l): # type: ignore
        _frozen_exc()

    def __hash__(self):
        return hash(tuple(self))

class frozendict(dict):
    def __setitem__(self, i, val):
        _frozen_exc()

    def __delitem__(self, i):
        _frozen_exc()

    def update(self, i):
        _frozen_exc()

    def __hash__(self):
        return hash(tuple(self.items()))

    # TODO: other APIs
