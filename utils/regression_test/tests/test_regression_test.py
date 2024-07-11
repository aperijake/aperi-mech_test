import os
import unittest
from regression_test import RegressionTest

class TestRegressionTest(unittest.TestCase):

	def test_run_executable_fail(self):
		# Change to the directory where the test files are located
		os.chdir('tests/test_files')

		# Setup
		test = RegressionTest('fail_test', 'aperi-mech', 1, ['input.yaml'], 'exodiff', 'compare.exodiff', 'results.exo', 'bad_gold.exo', [])

		# Execute
		result = test.run()

		# Verify
		self.assertFalse(result)
		
        # Change back to the original directory
		os.chdir('../..')

	def test_run_executable_pass(self):
		# Change to the directory where the test files are located
		os.chdir('tests/test_files')

		# Setup
		test = RegressionTest('success_test', 'aperi-mech', 1, ['input.yaml'], 'exodiff', 'compare.exodiff', 'results.exo', 'good_gold.exo', [])

		# Execute
		result = test.run()

		# Verify
		self.assertTrue(result)

        # Change back to the original directory
		os.chdir('../..')

if __name__ == '__main__':
	unittest.main()