"""
Implementation of the coroutines from sections 1-3 of Knuth's paper

Command line runs to re-produce some of the tables in the paper

$ python trolls.py bump --N 3

$ python trolls.py ebump --N 6 --E 1 3 4

$ python trolls.py nudge --N 4
"""
import argparse

# Globals for easier communication
N = 6
M = 3
E = [1, 3, 4]
Lights = [0 for i in range(N)]


def initial_nudge_sequence(n):
    def infinite_string():
        while True:
            yield from [0, 0, 0]
            yield from [1, 1, 1]
    s = infinite_string()
    return [next(s) for i in range(n)]


def gwhile(coro, val=True):
    while val == next(coro):
        yield val


def poke(k):
    "Unrestricted Trolls"
    coro = poke(k-1) if k > 1 else None

    while True:
        Lights[k-1] = 1 - Lights[k-1]
        yield True
        yield next(coro) if coro else False


def bump(k):
    "Chain 1->2->...->n"
    coro = bump(k+1) if k < N else None

    while True:
        # awake 0
        if k < N:
            yield from gwhile(coro)
        Lights[k-1] = 1
        yield True

        # asleep 1
        yield False

        # awake 1
        Lights[k-1] = 0
        yield True

        # asleep 0
        if k < N:
            yield from gwhile(coro)
        yield False


def cobump(k):
    "Chain n->n-1->...->1"
    coro = cobump(k+1) if k < N else None

    while True:
        # awake 0
        Lights[k-1] = 1
        yield True

        # asleep 1
        if k < N:
            yield from gwhile(coro)
        yield False

        # awake 1
        if k < N:
            yield from gwhile(coro)
        Lights[k-1] = 0
        yield True

        # asleep 0
        yield False


def mbump(k):
    "Chain: n->n-1->...->m+1->1->2->...->m"
    kcoro = mbump(k+1) if k < N else None
    mcoro = mbump(M+1) if k == 1 and M < N else None

    while True:
        # awake 0
        if k < M:
            yield from gwhile(kcoro)

        Lights[k-1] = 1
        yield True

        # asleep 1
        if M < k < N:
            yield from gwhile(kcoro)
        if k == 1 and M < N:
            yield from gwhile(mcoro)
        yield False

        # awake 1
        if M < k < N:
            yield from gwhile(kcoro)
        if k == 1 and M < N:
            yield from gwhile(mcoro)
        Lights[k-1] = 0
        yield True

        # asleep 0
        if k < M:
            yield from gwhile(kcoro)
        yield False


def ebump(k):
    "Several separate chain defined by endpoints E"
    kcoro = ebump(k+1) if k < N and k+1 not in E else None
    ecoro = ebump(E[E.index(k)-1]) if k > 1 and k in E else None

    while True:
        # awake 0
        if kcoro:
            yield from gwhile(kcoro)
        Lights[k-1] = 1
        yield True

        # asleep 0
        yield next(ecoro) if ecoro else False

        # awake 1
        Lights[k-1] = 0
        yield True

        # asleep 0
        if kcoro:
            yield from gwhile(kcoro)
        yield next(ecoro) if ecoro else False


def nudge(k):
    "Fence digraphs"
    kp = k + 2 - (k % 2)   # k + 1 if odd(k) else k + 2
    kpp = k + 1 + (k % 2)  # k + 2 if odd(k) else k + 1

    kp_coro = nudge(kp) if kp <= N else None
    kpp_coro = nudge(kpp) if kpp <= N else None

    # use nested generators to start at appropriate point
    def awake0():
        if kp_coro:
            yield from gwhile(kp_coro)
        Lights[k-1] = 1
        yield True

    def asleep1():
        if kpp_coro:
            yield from gwhile(kpp_coro)
        yield False

    def awake1():
        if kpp_coro:
            yield from gwhile(kpp_coro)
        Lights[k-1] = 0
        yield True

    def asleep0():
        if kp_coro:
            yield from gwhile(kp_coro)
        yield False

    if Lights[k-1] == 1:
        yield from awake1()
        yield from asleep0()

    while True:
        yield from awake0()
        yield from asleep1()
        yield from awake1()
        yield from asleep0()


def print_lights(*args):
    print(*Lights, sep='', end='  ')
    print(*args, sep=' ')


def driver(coro, n=N, m=M, e=E, seq=None):

    global N, M, E, Lights
    M = m
    E = sorted(e)
    if seq is None:
        N = n
        Lights = [0 for i in range(N)]
    else:
        N = len(seq)
        Lights = seq

    print_lights("Initial")

    # Run coro forwards and backwards
    while next(coro):
        print_lights(True)
    print_lights(False)

    while next(coro):
        print_lights(True)
    print_lights(False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('case',
                        type=str,
                        choices=("poke", "bump", "cobump",
                                 "mbump", "ebump", "nudge"),
                        help="coroutine case from knuth paper")
    parser.add_argument('--N',
                        type=int,
                        help="Number of 'Trolls'",
                        default=4)
    parser.add_argument('--M',
                        type=int,
                        help="constraint for mbump case",
                        default=2)
    parser.add_argument('--E',
                        type=int,
                        nargs='*',
                        help="set of digraph endpoints for case ebump")

    args = parser.parse_args()

    if args.case == "poke":
        driver(poke(args.N), n=args.N)
    elif args.case == "bump":
        driver(bump(1), n=args.N)
    elif args.case == "cobump":
        driver(cobump(1), n=args.N)
    elif args.case == "mbump":
        if args.M is None:
            raise RuntimeError("--M must be specified for `mbump`")
        driver(mbump(1), n=args.N, m=args.M)
    elif args.case == "ebump":
        if not args.E:
            raise RuntimeError("--E must be specfied for `ebump`")
        if max(args.E) > args.N:
            raise RuntimeError("--N must be large enough to accomidate endpoint set")
        driver(ebump(max(args.E)), n=args.N, e=args.E)
    elif args.case == "nudge":
        driver(nudge(1), seq=initial_nudge_sequence(args.N))
