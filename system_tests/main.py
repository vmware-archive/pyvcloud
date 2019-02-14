import os
import sys
import unittest
import xmlrunner


if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    root_dir = os.path.dirname(__file__)
    stable_tests = []
    for test in sys.argv[1:]:
        if test.find('.py'):
            test = test.replace('.py', '')
        stable_tests.append(test)
    testRunner = xmlrunner.XMLTestRunner(output=root_dir + 'test-reports')
    package = test_loader.loadTestsFromNames(names=stable_tests)

    try:
        testRunner.run(package)
    except Exception as e:
        print(e)


