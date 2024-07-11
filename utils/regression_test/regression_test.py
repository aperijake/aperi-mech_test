import argparse
import subprocess
import os
import sys
import datetime
import time

def _log_output(log_file, message):
    with open(log_file, 'a') as f:
        f.write(message)

def _run_executable(command_pre, executable_path, command_args, log_file):
    return_code = 1

    error_message = None

    try:
        # Run the executable with additional arguments
        command = command_pre + [executable_path] + command_args
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Capture stdout and stderr
        stdout, stderr = process.communicate()
        
        # Wait for the process to finish and get the return code
        return_code = process.wait()
        
        # Check the return code
        if return_code == 0:
            _log_output(log_file, "Executable ran successfully.\nPASSED\n")
        else:
            error_message = f"Executable returned non-zero exit code: {return_code}"
            error_message += f"\nCommand: {' '.join(command)}"
            error_message += "\nFAILED"
            _log_output(log_file, error_message)
            print(error_message)
        
        if stdout:
            _log_output(log_file, "Standard output:\n" + stdout.decode())
        if stderr:
            _log_output(log_file, "Standard error:\n" + stderr.decode())
    
    except FileNotFoundError:
        _log_output(log_file, f"Executable not found at path: {executable_path}")
        print(f"Executable not found at path: {executable_path}")
    except Exception as e:
        _log_output(log_file, f"An error occurred: {e}")
        print(f"An error occurred: {e}")

    return return_code

def _remove_file(filename):
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass
    # Make sure the file was removed
    if os.path.exists(filename):
        print(f"Failed to remove {filename}")
        sys.exit(1)

def _get_date_time():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")


class RegressionTest:

    def __init__(self, test_name, executable_path, num_procs, exe_args, exodiff_path, exodiff_file, exodiff_results_file, exodiff_gold_results_file, exodiff_args):
        self.test_name = test_name
        self.executable_path = executable_path
        self.num_procs = num_procs
        self.exe_args = exe_args
        self.exodiff_path = exodiff_path
        self.exodiff_file = exodiff_file
        self.exodiff_results_file = exodiff_results_file
        self.exodiff_gold_results_file = exodiff_gold_results_file
        self.exodiff_args = exodiff_args
        self.executable_time = 0

    def run(self):
        _remove_file('run_test.log')
        _remove_file(self.exodiff_results_file)
        return_code = self._run_executable()
        if return_code == 0:
            return_code = self._run_exodiff()
        passed = self._check_return_code(return_code)
        self._move_log_files()
        return passed

    def _move_log_files(self):
        # Move run_test.log to a unique name with the date and time
        date_time = _get_date_time()
        log_file = self.test_name + '_' + date_time + '.log'
        os.rename('run_test.log', log_file)

    def _check_return_code(self, return_code):
        GREEN = '\033[92m'  # Green text
        RED = '\033[91m'   # Red text
        RESET = '\033[0m'  # Reset color

        passed = 0

        if return_code == 0:
            print(f"{GREEN}PASS:{RESET}    time(s): {self.executable_time:.4e}    test: {self.test_name:<20}")
            passed = 1
        else:
            print(f"{RED}FAIL:{RESET}    time(s): {self.executable_time:.4e}    test: {self.test_name:<20}")
            print(f"Return code: {return_code}")

        return passed

    def _run_executable(self):
        command_pre = ['mpirun', '-n', str(self.num_procs)]
        # Time the executable
        start_time = time.perf_counter()
        return_code = _run_executable(command_pre, self.executable_path, self.exe_args, 'run_test.log')
        end_time = time.perf_counter()
        self.executable_time = end_time - start_time
        return return_code

    def _run_exodiff(self):
        return _run_executable([], self.exodiff_path, ['-f', self.exodiff_file, self.exodiff_results_file, self.exodiff_gold_results_file] + self.exodiff_args, 'run_test.log')

def _parse_arguments():
    # Define command line arguments
    parser = argparse.ArgumentParser(description='Run an executable and check its return value.')
    parser.add_argument('--name', help='Name of the test', default='test')
    parser.add_argument('--num_procs', help='Number of processors for running the executable', default=1)
    parser.add_argument('--executable_path', help='Path to the executable', default='aperi-mech')
    parser.add_argument('--exodiff_path', help='Path to exodiff', default='exodiff')
    parser.add_argument('--exodiff_file', help='Path to exodiff file.', default='compare.exodiff')
    parser.add_argument('--exodiff_gold_file', help='Path to exodiff gold file.', default='gold_results.exo')
    parser.add_argument('--exodiff_results_file', help='Path to exodiff results file.', default='results.exo')
    parser.add_argument('--exe_args', nargs='*', help='Additional arguments to pass to the executable')
    parser.add_argument('--exodiff_args', nargs='*', help='Additional arguments to pass to exodiff')
    
    # Parse command line arguments
    return parser.parse_args()

def main():
    args = _parse_arguments()
    regression_test = RegressionTest(args.name, args.executable_path, args.num_procs, args.exe_args, args.exodiff_path, args.exodiff_file, args.exodiff_args)
    return_code = regression_test.run()
    return return_code

if __name__ == "__main__":
    return_code = main()
    exit(return_code)