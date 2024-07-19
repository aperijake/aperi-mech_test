#!/usr/bin/env python3
import os
import time
import argparse
import yaml
import sys
import glob
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
    inputs['runtime_tolerance_percent'] = yaml_node['runtime_tolerance_percent']
    inputs['memory_tolerance_percent'] = yaml_node['memory_tolerance_percent']

    return inputs

def run_performance_tests_from_directory(root_dir, build_dir, gpu_only=False, cpu_only=False, cpu_procs=None, skip_csv=False, update_baseline=False):
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
                    if test_config['hardware'] == 'gpu' and cpu_only:
                        print(f"  Skipping test {test_config['hardware']}_{test_config['num_processors']}. --cpu set")
                        continue
                    if test_config['hardware'] == 'cpu' and gpu_only:
                        print(f"  Skipping test {test_config['hardware']}_{test_config['num_processors']}. --gpu set")
                        continue
                    if cpu_procs and not(int(cpu_procs) == int(test_config['num_processors'])):
                        print(f"  Skipping test {test_config['hardware']}_{test_config['num_processors']}. Request only tests with {cpu_procs} processors.")
                        continue
                    print(f"  Running test {test_config['hardware']}_{test_config['num_processors']}")
                    inputs = get_inputs_from_yaml_node(test_config, os.path.basename(dirpath), build_dir)
                    # Command:
                    command = ['python3', script_path+'/utils/performance_test/performance_test.py',
                               '--n', str(inputs['num_runs']),
                               '--np', str(inputs['num_processors']),
                               '--time-tolerance', str(inputs['runtime_tolerance_percent']),
                               '--memory-tolerance', str(inputs['memory_tolerance_percent']),
                               '--no-plot',
                               '--no-ask']
                    if not skip_csv:
                        command.append('--csv')
                    if update_baseline:
                        command.append('--update-baseline')
                    command.append(inputs['executable_path'])
                    command.append(inputs['input_file'])

                    # Run the command
                    return_code = subprocess.call(command)
                    if return_code == 0:
                        passing_tests += 1
                    total_tests += 1
            print("-----------------------------------\n")
            # Change back to the original directory
            os.chdir(current_dir)
    return passing_tests, total_tests

def clean_logs(root_dir):
    for dirpath, _dirnames, filenames in os.walk(root_dir):
        if 'performance.yaml' in filenames:
            print("-----------------------------------")
            print(f"Cleaning logs in {dirpath}")
            # Use glob to find all files matching the pattern
            for log_file in glob.glob(f"{dirpath}/regression*.log"):
                os.remove(log_file)  # Remove each matching file
            print("-----------------------------------\n")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run regression tests.')
    parser.add_argument('-d', '--dir', nargs='+', help='Directory root containing the tests. Will recursively search for test.yaml files.', default='.')
    parser.add_argument('--build_dir', help='Directory containing the build', default='/home/azureuser/projects/aperi-mech/build/')
    parser.add_argument('--clean_logs', help='Clean logs in the directory', action='store_true')
    parser.add_argument('--gpu', help='Only run GPU tests', action='store_true')
    parser.add_argument('--cpu', help='Only run CPU tests', action='store_true')
    parser.add_argument('--cpu_num_procs', help='Only run CPU tests with this number of processors', default=None)
    parser.add_argument('--skip_csv', help='Skip putting reuslts in the csv file.', action='store_true')
    parser.add_argument('--update_baseline', help='Update the baseline results.', action='store_true')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    directories = [os.path.abspath(d) for d in args.dir]

    # Just clean the logs and exit
    if (args.clean_logs):
        for directory in directories:
            clean_logs(directory)
        sys.exit(0)

    # full path to the build directory
    build_dir = os.path.abspath(args.build_dir)

    # time the regression tests
    start_time = time.perf_counter()
    for directory in directories:
        passing_tests, total_tests = run_performance_tests_from_directory(directory, build_dir, args.gpu, args.cpu, args.cpu_num_procs, args.skip_csv, args.update_baseline)
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
