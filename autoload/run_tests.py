#!/usr/bin/env python

import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tsurf.tests import tests

tests.run()
