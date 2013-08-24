import types

def make_decorator(func, *dec_args):
    def decorator(undecorated):
        def decorated(*args, **kargs):
            return func(undecorated, args, kargs, *dec_args) 
        
        decorated.__name__ = undecorated.__name__
        return decorated
    
    decorator.__name__ = func.__name__
    return decorator

def make_decorator_with_args(func):
    def decorator_with_args(*dec_args):
        return make_decorator(func, *dec_args)
    return decorator_with_args

decorator           = make_decorator
decorator_with_args = make_decorator_with_args


@decorator_with_args
def do(func, func_args, func_kargs, Monad):
    @handle_monadic_throws(Monad)
    def run_maybe_iterator():
        itr = func(*func_args, **func_kargs)

        if isinstance(itr, types.GeneratorType):
            @handle_monadic_throws(Monad)
            def send(val):
                try:
                    # here's the real magic
                    monad = itr.send(val) 
                    return Monad.bind(monad, send)
                except StopIteration:
                    return Monad.unit(None)
                
            return send(None)
        else:
            #not really a generator
            if itr is None:
                return Monad.unit(None)
            else:
                return itr

    return run_maybe_iterator()

@decorator_with_args
def handle_monadic_throws(func, func_args, func_kargs, Monad):
    try:
        return func(*func_args, **func_kargs)
    except MonadReturn, ret:
        return Monad.unit(ret.value)
    except Done, done:
        assert isinstance(done.monad, Monad)
        return done.monad

class MonadReturn(Exception):
    def __init__(self, value):
        self.value = value
        Exception.__init__(self, value)

class Done(Exception):
    def __init__(self, monad):
        self.monad = monad
        Exception.__init__(self, monad)

def mreturn(val):
    raise MonadReturn(val)

def done(val):
    raise Done(val)

##### Disjoint SUMBITCH ####

class BadArgs(Exception):
    def __init__(self, value):
        self.value = value
        Exception.__init__(self, value)

def printer(j):
    print j

class Sum:
    def __init__(self, *args, **kargs):
        if len(args) == 0:
            self.args = [None]
        else: 
            self.args = args
        self.kargs = kargs

    def switch(self, **kargs):
        return kargs[ self.__class__.__name__ ](*self.args, **self.kargs)

class Maybe:
    class Just(Sum): pass
    class Nothing(Sum): pass

    @classmethod
    def unit(cls, val):
        return Maybe.Just(val)

    @classmethod
    def to_string(cls, obj):
        return obj.switch( Nothing = lambda _ : "Nothing"
                         , Just    = lambda r : "Just(%r)" % r
                         )
    @classmethod
    def bind(cls, obj, bindee):
        return obj.switch( Nothing = lambda _ : obj
                         , Just    = lambda r : bindee(r))
    

def failable_monad_example():
    def fdiv(a, b):
        if b == 0:
            return Maybe.Nothing()
        else:
            return Maybe.Just(a / b)

    @do(Maybe)
    def with_failable(first_divisor):
        val1 = yield fdiv(2.0, first_divisor)
        
        val2 = yield fdiv(3.0, 1.0)
        val3 = yield fdiv(val1, val2)
        mreturn(val3)

    print Maybe.to_string(with_failable(0.0))
    print Maybe.to_string(with_failable(1.0))

failable_monad_example()
