#!/usr/bin/env python

import sys
import os
import time
import unittest
import logging
import pprint
import subprocess

from deduplicate import dedup

logging.basicConfig(file=sys.stdout,
                    format='%(levelname)s %(funcName)s %(lineno)s %(message)s',
                    level=logging.INFO)

class TestDedup(unittest.TestCase):
    def setUp(self):
        self.funcname = '_'.join(self.id().split('.')[-2:])

    def test01(self):
        infile = 'testfiles/474_0_0.txt'
        names, seqs = zip(*(line.split() for line in open(infile) if line.strip()))

        d1 = dedup(seqs)
        d2 = dedup(seqs, chunksize=500)

        as_strings = lambda idx: set(seqs[i] for i in idx)
        self.assertTrue(as_strings(d1.keys()) == as_strings(d1.keys()))

        parents = [seqs[i] for i in d1.keys()]
        # canonical sequences should all be unique
        self.assertTrue(len(parents) == len(set(parents)))
        dp = dedup(parents)
        self.assertTrue(len(dp) == len(parents))

        
