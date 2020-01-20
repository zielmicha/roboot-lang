
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

class lazy_it:
    def __init__(self, it):
        self.it = iter(it)
        self.lst = []

    def __iter__(self):
        i = 0
        while True:
            if len(self.lst) <= i:
                self.lst.append(next(self.it))

            yield self.lst[i]
            i += 1

class Combinator:
    def __add__(self, a):
        return _concat(self, a)

    def __or__(self, a):
        return _either(self, a)

    def __init__(self, f):
        self.f = f

    def _run(self, x):
        if (self, x) not in x.memo:
            x.memo[self, x] = lazy_it(self.f(x)) # should be lazy

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
        for r, text1 in a._run(text):
            yield g(r), text1

    return Combinator(f)

def _concat(a, b):
    def f(text):
        for r_a, text1 in a._run(text):
            for r_b, text2 in b._run(text1):
                yield (r_a + r_b, text2)

    return Combinator(f)

def _either(a, b):
    def f(text):
        yield from a._run(text)
        yield from b._run(text)

    return Combinator(f)

def lazy_combinator(g):
    g_lazy = Lazy(g)
    def f(text):
        return g_lazy.value._run(text)

    return Combinator(f)

def nothing():
    def f(text):
        yield ((), text)

    return Combinator(f)

inf = float('inf')

def many(op, n_min=0, n_max=inf):
    if n_min == 0 and n_max == inf:
        # optimization
        this = ForwardDecl()
        this.value = (op + this) | nothing()
        return this

    x = (op + lazy_combinator(lambda: many(op, n_min - 1, n_max - 1)))
    if n_min <= 0:
        return x | nothing()
    else:
        return x

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
    r = lazy_it(cat._run(Input(memo, text, 0)))

    result = next(iter(r))

    print(len(memo), sum( len(v.lst) for v in memo.values() ))
    for k,v in sorted(memo.items(), key=lambda i: len(i[1].lst))[::-1][:10]:
        print('max', k, len(v.lst))
        #print('       ', v.lst[:3])

    return result

if __name__ == '__main__':

    def char(c):
        def f(text):
            if text and text[0] == c: yield (c,), text[1:]
        return combinator(f)

    # cat = many(char('f')) + char('e')
    # text = 'f'*10 + 'e'
    inner = joined_with(char('+'), char('f'))
    cat = joined_with(char('*'), inner) + char('e')
    text = '+'.join(['f'] * 7) + 'e'
    for i in run(cat, text):
        print(i)
