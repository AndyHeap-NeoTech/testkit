"""
Defines stub suites
"""

import unittest
import tests.stub.retry as retry
import tests.stub.sessiondisconnected as sessiondisconnected

loader = unittest.TestLoader()

stub_suite = unittest.TestSuite()
stub_suite.addTests(loader.loadTestsFromModule(retry))
stub_suite.addTests(loader.loadTestsFromModule(sessiondisconnected))
