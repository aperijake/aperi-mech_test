#!python

import sys
sys.path.append('../utils')
import run_test

if __name__ == "__main__":

    passing_tests = 0
    total_tests = 0

    # Run cpu, 1 proc
    regression_1_proc = run_test.RegressionTest('smallest_taylor_bar_reproducing_kernel_1_proc', 'aperi-mech', 1, ['input.yaml'], 'exodiff', 'compare.exodiff', 'results.exo', 'gold_results.exo', [])
    passing_tests += regression_1_proc.run()
    total_tests += 1

    # Run cpu, 4 procs
    regression_4_proc = run_test.RegressionTest('smallest_taylor_bar_reproducing_kernel_4_procs', 'aperi-mech', 4, ['input.yaml'], 'exodiff', 'compare.exodiff', 'results.exo', 'gold_results.exo', [])
    passing_tests += regression_4_proc.run()
    total_tests += 1

    # Run gpu, 1 proc
    regression_gpu = run_test.RegressionTest('smallest_taylor_bar_reproducing_kernel_gpu', '/home/azureuser/projects/aperi-mech/build/Release_gpu/aperi-mech', 1, ['input.yaml'], 'exodiff', 'compare.exodiff', 'results.exo', 'gold_results.exo', [])
    passing_tests += regression_gpu.run()
    total_tests += 1

    failing_tests = total_tests - passing_tests

    if failing_tests > 0:
        print(f"{failing_tests} tests failed.")
        print(f"{passing_tests} tests passed.")
        sys.exit(1)
    else:
        print("All " + str(passing_tests) + " tests passed.")
        sys.exit(0)