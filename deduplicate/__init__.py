__version__ = "0.1.1"
__version_info__ = tuple([ int(num) for num in __version__.split('.')])

_min_python_version = '2.7.0'

def _check_python_version():
    vsplit = lambda x: tuple([int(n) for n in x.split('.')])
    sys_version = sys.version.split()[0]
    version = vsplit(sys_version)
    if version < vsplit(_min_python_version):
        raise SystemError('this package requires Python version %s or greater (current version is %s)' \
                              % (_min_python_version, sys_version))

import time
import logging
import operator
import sys
from itertools import izip, chain, repeat, islice, takewhile, izip_longest

log = logging

_check_python_version()

def grouper(n, iterable, pad=True):
    """
    Return sequence of n-tuples composed of successive elements
    of iterable; last tuple is padded with None if necessary. Not safe
    for iterables with None elements.
    """

    args = [iter(iterable)] * n
    iterout = izip_longest(fillvalue=None, *args)

    if pad:
        return iterout
    else:
        return (takewhile(lambda x: x is not None, c) for c in iterout)

def flatten(d):
    return sorted(d.keys() + list(chain(*d.values())))

#### the real work is done in coalesce and merge

def coalesce(strings, idx=None, comp='contains', log=log):

    """
    Groups a collection of strings by identifying the longest string
    representing each nested set of substrings (if comp='contains') or
    into sets of identical strings (if comp='eq')

    Input
    =====

     * strings - a tuple of N strings
     * comp - 'contains' (default) or 'eq'
     * log - a logging object; defualt is the root logger

     Output
     ======

     * a dict keyed by indices in strings. Each key i returns a list of
       indices corresponding to strings nested within (or identical to) the
       string at strings[i].
    """

    start = time.time()

    try:
        len(strings)
    except TypeError:
        strings = list(strings)
    
    if not idx:
        idx = range(len(strings))
            
    # sort idx by length, descending
    idx.sort(key=lambda i: len(strings[i]),reverse=True)
    log.debug('sort completed at %s secs' % (time.time()-start))
    nstrings = len(idx)

    d = dict((i,list()) for i in idx)

    # operator.eq(a,b) <==> a == b
    # operator.contains(a,b) <==> b in a
    compfun = getattr(operator, comp)

    cycle = 0
    while len(idx) > 0:
        parent_i = idx.pop(0)
        parent_str = strings[parent_i]
        children = set(i for i in idx if compfun(parent_str,strings[i]))
        d[parent_i].extend(children)
        idx = [x for x in idx if x not in children]

    for i in chain(*d.values()):
        del d[i]

    log.info('Coalesce %s strings to %s in %.2f secs' % (nstrings, len(d), time.time()-start))

    return d

def merge(strings, d1, d2=None, comp='contains'):

    """
    Merge two dictionaries mapping superstrings to substrings.

    Input
    =====

     * strings - a tuple of N strings
     * d1, d2 - output of coalesce()
     * comp - type of string comparison, passed to coalesce ("contains" or "eq")

    Output
    ======

     * a single dict mapping superstrings to substrings

    """

    if d2 is None:
        log.warning('d2 not provided, returning d1')
        return d1

    d = coalesce(strings, idx=d1.keys()+d2.keys(), comp=comp)

    for i, dvals in d.items():
        if dvals:
            d[i].extend(list(chain(*[d1.get(j,[]) for j in dvals])))
            d[i].extend(list(chain(*[d2.get(j,[]) for j in dvals])))
        d[i].extend(d1.get(i,[]))
        d[i].extend(d2.get(i,[]))

    if __debug__:
        d1Flat, d2Flat, dFlat = flatten(d1), flatten(d2), flatten(d)
        log.info('checking d of length %s with min,max=%s,%s' % \
            (len(d),min(dFlat),max(dFlat)))

        assert set(d1Flat + d2Flat) == set(dFlat)

        for parent, children in d.items():
            for child in children:
                assert strings[child] in strings[parent]

    return d

def dedup(strings, comp='contains', chunksize=None):

    """
    Given a sequence of strings, return a dictionary mapping
    superstrings to substrings.

    Input
    =====

     * strings - a tuple of N strings
     * comp - defines string comparison method:

       * 'contains' -> "s1 in s2" or
       * 'eq' -> "s1 == s2"

     * chunksize - an integer defining size of partitions into which
       strings are divided; each partition is coalesced individually,
       and the results of each are merged.

    Output
    ======

     * A dict mapping superrstrings to substrings, in which keys and
     values are indices into strings.

    """

    nstrings = len(strings)

    if not chunksize:
        chunksize = nstrings

    chunks = grouper(n=chunksize, iterable=xrange(nstrings), pad=False)
    # TODO: parallelize me
    coalesced = [coalesce(strings, idx=list(c), comp=comp) for c in chunks]

    cycle = 1
    while len(coalesced) > 1:
        log.warning('merge cycle %s, %s chunks' % (cycle,len(coalesced)))
        # TODO: parallelize me
        coalesced = [merge(strings, d1, d2, comp=comp) for d1,d2 in grouper(n=2, iterable=coalesced)]
        cycle += 1

    d = coalesced[0]

    assert set(flatten(d)) == set(range(nstrings))

    return d



