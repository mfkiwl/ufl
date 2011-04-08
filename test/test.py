#!/usr/bin/env python
"""Run all tests"""

__author__ = "Martin Alnes (martinal@simula.no) and Anders Logg (logg@simula.no)"
__date__ = "2008-03-12 -- 2011-04-08"

def discover_tests(args):
    import glob
    # Running tests from all test_foo.py files
    tests = sorted(f.replace(".py", "") for f in glob.glob("test_*.py"))

    # Demos are slow, allow running everything else easily...
    tests.remove("test_analyse_demos")
    # ... and always check demos last
    if not "skipdemos" in args:
        tests.append("test_analyse_demos")

    return tests

def configureLogging():
    # Emit all messages, show nothing on screen,
    # but write everything to log file
    import logging
    from ufl.log import ufl_logger
    sh = ufl_logger.get_handler()
    fh = ufl_logger.add_logfile(level = logging.DEBUG)

    ufl_logger.set_level(logging.DEBUG)
    sh.setLevel(logging.CRITICAL)
    #fh.setLevel(logging.DEBUG)

def run_suite(tests):
    import unittest
    assert tests
    loader = unittest.TestLoader()
    modules = [__import__(test) for test in tests]
    suite = loader.loadTestsFromModule(modules[0])
    for m in modules[1:]:
        suite.addTests(loader.loadTestsFromModule(m))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

def main(args):
    tests = discover_tests(args)
    configureLogging()
    return run_suite(tests)

if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
