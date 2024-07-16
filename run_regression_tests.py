#!/usr/bin/env python3
import os
import time
import argparse
import yaml
import sys
import glob
sys.path.append('utils')
from regression_test import RegressionTest, ExodiffCheck, PeakMemoryCheck

def get_inputs_from_yaml_node(yaml_node, test_name_prefix, build_dir):
    inputs = {}

    # test name is directory + hardware + number of processors
    inputs['test_name'] = test_name_prefix + '_' + yaml_node['hardware'] + '_np_' + str(yaml_node['num_processors'])
    inputs['input_file'] = yaml_node['input_file']
    memory_node = yaml_node.get('peak_memory_check', None)
    if memory_node is not None:
        inputs['peak_memory'] = memory_node['value']
        inputs['peak_memory_percent_tolerance'] = memory_node['percent_tolerance']
    else:
        inputs['peak_memory'] = None
        inputs['peak_memory_percent_tolerance'] = None
    inputs['exodiff'] = []
    exodiff_list = yaml_node['exodiff']
    for exodiff in exodiff_list:
        exodiff_args = {}
        exodiff_args['compare_file'] = exodiff['compare_file']
        exodiff_args['results_file'] = exodiff['results_file']
        exodiff_args['gold_file'] = exodiff['gold_file']
        inputs['exodiff'].append(exodiff_args)

    inputs['executable_path'] = build_dir + '/Release/aperi-mech'
    if yaml_node['hardware'] == 'gpu':
        inputs['executable_path'] = build_dir + '/Release_gpu/aperi-mech'
    inputs['num_processors'] = yaml_node['num_processors']

    return inputs

def run_regression_tests_from_directory(root_dir, build_dir):
    passing_tests = 0
    total_tests = 0
    
    # Store the current directory
    current_dir = os.getcwd()

    for dirpath, _dirnames, filenames in os.walk(root_dir):
        if 'test.yaml' in filenames:
            # Change to the directory where the test files are located
            os.chdir(dirpath)
            print("-----------------------------------")
            print(f"Running tests in {dirpath}")
            with open('test.yaml', 'r') as file:
                yaml_node = yaml.safe_load(file)
                test_configs = yaml_node['tests']
                for test_config in test_configs:
                    print(f"  Running test {test_config['hardware']}_{test_config['num_processors']}")
                    inputs = get_inputs_from_yaml_node(test_config, os.path.basename(dirpath), build_dir)
                    regression_test = RegressionTest(inputs['test_name'], inputs['executable_path'], inputs['num_processors'], [inputs['input_file']])
                    return_code, stats = regression_test.run()
                    if return_code == 0:
                        num_exodiff = 0
                        all_exodiff_passed = True
                        for exodiff in inputs['exodiff']:
                            exodiff_check = ExodiffCheck(inputs['test_name']+"_exodiff_"+str(num_exodiff), 'exodiff', exodiff['compare_file'], exodiff['results_file'], exodiff['gold_file'], [])
                            return_code = exodiff_check.run()
                            if return_code != 0:
                                all_exodiff_passed = False
                        memcheck_passed = True
                        if inputs['peak_memory'] is not None:
                            peak_memory_check = PeakMemoryCheck(inputs['test_name']+"_peak_memory", stats["peak_memory"], inputs['peak_memory'], inputs['peak_memory_percent_tolerance'])
                            return_code = peak_memory_check.run()
                            if return_code != 0:
                                memcheck_passed = False
                        if all_exodiff_passed and memcheck_passed:
                            passing_tests += 1
                            print("\033[92m  PASS\033[0m")
                        else:
                            print("\033[91m  FAIL\033[0m")
                    else:
                        print("\033[91m  FAIL\033[0m")
                    total_tests += 1
            print("-----------------------------------\n")
            # Change back to the original directory
            os.chdir(current_dir)
    return passing_tests, total_tests

def clean_logs(root_dir):
    for dirpath, _dirnames, filenames in os.walk(root_dir):
        if 'test.yaml' in filenames:
            print("-----------------------------------")
            print(f"Cleaning logs in {dirpath}")
            # Use glob to find all files matching the pattern
            for log_file in glob.glob(f"{dirpath}/regression*.log"):
                os.remove(log_file)  # Remove each matching file
            print("-----------------------------------\n")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run regression tests.')
    parser.add_argument('--directory', help='Directory root containing the tests. Will recursively search for test.yaml files.', default='.')
    parser.add_argument('--build_dir', help='Directory containing the build', default='/home/azureuser/projects/aperi-mech/build/')
    parser.add_argument('--clean_logs', help='Clean the log files from the tests', action='store_true')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    # full path to the build directory
    build_dir = os.path.abspath(args.build_dir)

    directory = os.path.abspath(args.directory)

    # Just clean the logs and exit
    if (args.clean_logs):
        # full path
        clean_logs(directory)
        sys.exit(0)

    # time the regression tests
    start_time = time.perf_counter()
    passing_tests, total_tests = run_regression_tests_from_directory(directory, build_dir)
    end_time = time.perf_counter()
    print(f"Total time: {end_time - start_time:.4e} seconds")

    failing_tests = total_tests - passing_tests

    if failing_tests > 0:
        print(f"{failing_tests} tests failed.")
        print(f"{passing_tests} tests passed.")
        sys.exit(1)
    else:
        print(f"All {passing_tests} tests passed.")
        sys.exit(0)
