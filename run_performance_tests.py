#!/usr/bin/env python3
import os
import time
import argparse
import yaml
import sys
import subprocess

# Script path
script_path = os.path.dirname(os.path.realpath(__file__))

def get_inputs_from_yaml_node(yaml_node, test_name_prefix, build_dir):
    inputs = {}

    # test name is directory + hardware + number of processors
    inputs['test_name'] = test_name_prefix + '_' + yaml_node['hardware'] + '_np_' + str(yaml_node['num_processors'])
    inputs['input_file'] = yaml_node['input_file']
    inputs['executable_path'] = build_dir + '/Release/aperi-mech'
    if yaml_node['hardware'] == 'gpu':
        inputs['executable_path'] = build_dir + '/Release_gpu/aperi-mech'
    inputs['num_processors'] = yaml_node['num_processors']
    inputs['num_runs'] = yaml_node['num_runs']
    inputs['tolerance_percent'] = yaml_node['tolerance_percent']

    return inputs

def run_performance_tests_from_directory(root_dir, build_dir):
    passing_tests = 0
    total_tests = 0
    
    # Store the current directory
    current_dir = os.getcwd()

    for dirpath, _dirnames, filenames in os.walk(root_dir):
        if 'performance.yaml' in filenames:
            # Change to the directory where the test files are located
            os.chdir(dirpath)
            print("-----------------------------------")
            print(f"Running tests in {dirpath}")
            with open('performance.yaml', 'r') as file:
                yaml_node = yaml.safe_load(file)
                test_configs = yaml_node['tests']
                for test_config in test_configs:
                    print(f"  Running test {test_config['hardware']}_{test_config['num_processors']}")
                    inputs = get_inputs_from_yaml_node(test_config, os.path.basename(dirpath), build_dir)
                    # Command:
                    command = ['python3', script_path+'/utils/performance_test/performance_test.py',
                               '--n', str(inputs['num_runs']),
                               '--np', str(inputs['num_processors']),
                               '--tolerance', str(inputs['tolerance_percent']),
                               '--no-plot',
                               '--csv',
                               '--no-ask',
                               inputs['executable_path'],
                               inputs['input_file']]
                    # Run the command
                    return_code = subprocess.call(command)
                    if return_code == 0:
                        passing_tests += 1
                    total_tests += 1
            print("-----------------------------------\n")
            # Change back to the original directory
            os.chdir(current_dir)
    return passing_tests, total_tests

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run regression tests.')
    parser.add_argument('--directory', help='Directory root containing the tests. Will recursively search for test.yaml files.', default='.')
    parser.add_argument('--build_dir', help='Directory containing the build', default='/home/azureuser/projects/aperi-mech/build/')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    # full path to the build directory
    build_dir = os.path.abspath(args.build_dir)

    # time the regression tests
    start_time = time.perf_counter()
    passing_tests, total_tests = run_performance_tests_from_directory(args.directory, build_dir)
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
