#!/usr/bin/env python3
import os
import yaml
import sys
sys.path.append('utils')
from regression_test import RegressionTest

def get_inputs_from_yaml_node(yaml_node, test_name_prefix = ''):
	inputs = {}
	print(yaml_node)

    # test name is directory + hardware + number of processors
	inputs['test_name'] = test_name_prefix + '_' + yaml_node['hardware'] + '_np_' + str(yaml_node['num_processors'])
	inputs['input_file'] = yaml_node['input_file']
	inputs['exodiff'] = []
	exodiff_list = yaml_node['exodiff']
	for exodiff in exodiff_list:
		exodiff_args = {}
		exodiff_args['compare_file'] = exodiff['compare_file']
		exodiff_args['results_file'] = exodiff['results_file']
		exodiff_args['gold_file'] = exodiff['gold_file']
		inputs['exodiff'].append(exodiff_args)

	inputs['executable_path'] = '/home/azureuser/projects/aperi-mech/build/Release/aperi-mech'
	if yaml_node['hardware'] == 'gpu':
		inputs['executable_path'] = '/home/azureuser/projects/aperi-mech/build/Release_gpu/aperi-mech'
	inputs['num_processors'] = yaml_node['num_processors']

	return inputs

def run_regression_tests_from_directory(root_dir):
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
					inputs = get_inputs_from_yaml_node(test_config, os.path.basename(dirpath))
					# TODO(jake): only working for one exodiff check, need to generalize
					regression_test = RegressionTest(inputs['test_name'], inputs['executable_path'], inputs['num_processors'], [inputs['input_file']], 'exodiff', inputs['exodiff'][0]['compare_file'], inputs['exodiff'][0]['results_file'], inputs['exodiff'][0]['gold_file'], [])
					passing_tests += regression_test.run()
					total_tests += 1
            # Change back to the original directory
			os.chdir(current_dir)
			print("-----------------------------------\n")

	failing_tests = total_tests - passing_tests

	if failing_tests > 0:
		print(f"{failing_tests} tests failed.")
		print(f"{passing_tests} tests passed.")
		sys.exit(1)
	else:
		print(f"All {passing_tests} tests passed.")
		sys.exit(0)

if __name__ == "__main__":
	specified_directory = '.'
	run_regression_tests_from_directory(specified_directory)