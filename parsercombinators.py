
class Lazy:
    def __init__(self, f):
        assert f is not None
        self.__f = f
        self.__value = None

    @property
    def value(self):
        if self.__f:
            self.__value = self.__f()
            self.__f = None

        return self.__value

class Combinator:
    def __add__(self, a):
        return _concat(self, a)

    def __or__(self, a):
        return _either(self, a)

    def __init__(self, f):
        self.f = f

    def _run(self, x):
        if (self, x) not in x.memo:
            x.memo[self, x] = self.f(x)

        return x.memo[self, x]

    def map(self, g):
        return _map(self, g)

    def wrap(self):
        return self.map(lambda x: (x, ))

    def __repr__(self):
        return '<Combinator %r>' % self.f

def combinator(f):
    return Combinator(f)

def _map(a, g):
    def f(text):
        res = a._run(text)
        if res:
            r, text1 = res
            return g(r), text1

    return Combinator(f)

def _concat(a, b):
    def f(text):
        res = a._run(text)
        if res is None: return None
        r_a, text1 = res
        res = b._run(text1)
        if res is None: return None
        r_b, text2 = res
        return (r_a + r_b, text2)

    return Combinator(f)

def _either(a, b):
    def f(text):
        res = a._run(text)
        if res is None:
            return b._run(text)
        else:
            return res

    return Combinator(f)

def lazy_combinator(g):
    g_lazy = Lazy(g)
    def f(text):
        return g_lazy.value._run(text)

    return Combinator(f)

def nothing():
    def f(text):
        return ((), text)

    return Combinator(f)

inf = float('inf')

def many(op, n_min=0, n_max=inf):
    def f(text):
        result = []
        count = 0

        while True:
            if count == n_max: break

            res = op._run(text)
            if res is None: break
            value, text = res
            result += value
            count += 1

        if count < n_min or count > n_max:
            return None

        return tuple(result), text

    return Combinator(f)

def optional(x):
    return many(x, 0, 1)

def joined_with(sep, val):
    return many(val + sep) + val

class ForwardDecl(Combinator):
    def __init__(self):
        self.value = None

    def _run(self, x):
        return self.value._run(x)

class Input:
    def __init__(self, memo, text, offset):
        self.memo = memo
        self.text = text
        self.offset = offset
        assert self.offset >= 0 and self.offset <= len(self.text)

    def __getitem__(self, t):
        if isinstance(t, slice):
            assert t.step is None
            if t.stop is None:
                return Input(self.memo, self.text, self.offset + t.start)

            return self.text[self.offset + t.start : self.offset + t.stop]

        return self.text[self.offset + t]

    def __bool__(self):
        return self.offset < len(self.text)

    def __hash__(self):
        return hash((self.text, self.offset))

    def __eq__(self, o):
        if not isinstane(o, Input):
            return False

        return (self.text, self.offset) == (o.text, o.offset)

    def __repr__(self):
        return '<Input %d>' % self.offset

def run(cat, text):
    if isinstance(text, list): text = tuple(text)
    memo = {}
    result = cat._run(Input(memo, text, 0))
    if result is not None:
        return result[0]

if __name__ == '__main__':
    def char(c):
        def f(text):
            if text and text[0] == c: return (c,), text[1:]
        return combinator(f)

    print(run(optional(char('f')), ''))
    print(run(optional(char('f')), 'f'))
    print(run(optional(char('f')), 'ff'))

    # cat = many(char('f')) + char('e')
    # text = 'f'*10 + 'e'
    inner = joined_with(char('+'), char('f'))
    cat = joined_with(char('*'), inner) + char('e')
    text = '+'.join(['f'] * 1000) + 'e'
    #print(run(cat, text))
