import os
import unittest

from regression_test import ExodiffCheck, RegressionTest


class TestRegressionTest(unittest.TestCase):

    def setUp(self):
        os.chdir('tests/test_files')

    def tearDown(self):
        os.chdir('../..')

    def test_run_regression_test_fail(self):
        # Setup
        test = RegressionTest('fail_test', 'aperi-mech', 1, ['bad_input.yaml'])

        # Run the executable and verify the return code
        result = test.run()
        self.assertFalse(result == 0)

    def test_run_exodiff_check_fail(self):
        # Setup
        test = RegressionTest('fail_test', 'aperi-mech', 1, ['input.yaml'])
        exodiff = ExodiffCheck('fail_test', 'exodiff', 'compare.exodiff', 'results.exo', 'bad_gold.exo', [])

        # Run the executable and verify the return code
        result = test.run()
        self.assertTrue(result == 0)

        # Run exodiff and verify the return code
        result = exodiff.run()
        self.assertFalse(result == 0)

    def test_run_exodiff_check_success(self):
        # Setup
        test = RegressionTest('success_test', 'aperi-mech', 1, ['input.yaml'])
        exodiff = ExodiffCheck('success_test', 'exodiff', 'compare.exodiff', 'results.exo', 'good_gold.exo', [])

        # Run the executable and verify the return code
        result = test.run()
        self.assertTrue(result == 0)

        # Run exodiff and verify the return code
        result = exodiff.run()
        self.assertTrue(result == 0)

if __name__ == '__main__':
    unittest.main()