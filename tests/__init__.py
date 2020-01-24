import unittest
import os

def run():
    loader = unittest.TestLoader()
    tests = loader.discover(os.path.dirname(os.path.abspath(__file__)))
    testRunner = unittest.runner.TextTestRunner()
    testRunner.run(tests)
