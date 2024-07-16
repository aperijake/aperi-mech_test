import argparse
import subprocess
import os
import sys
import datetime
import time
import psutil

def _log_output(log_file, message):
    with open(log_file, 'a') as f:
        f.write(message)

def _run_executable(command_pre, executable_path, command_args, log_file, check_memory=False):
    return_code = 1
    error_message = None

    try:
        command = command_pre + [executable_path] + command_args
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Initialize peak memory usage variable
        peak_memory = 0
        stats = {}
        stats['peak_memory'] = 0

        if check_memory:
            # Wrap the subprocess with psutil to monitor memory usage
            ps_process = psutil.Process(process.pid)

            # Monitor memory usage as long as the process is running
            while process.poll() is None:
                total_memory = ps_process.memory_info().rss  # Memory of the main process
                for child in ps_process.children(recursive=True):
                    try:
                        child_mem = child.memory_info().rss
                        total_memory += child_mem  # Sum memory of all child processes
                    except psutil.NoSuchProcess:
                        continue  # Child process has finished and can no longer be queried
                peak_memory = max(peak_memory, total_memory)
                time.sleep(0.01)  # Adjust this value as needed

        stdout, stderr = process.communicate()
        return_code = process.wait()

        if return_code == 0:
            _log_output(log_file, "Executable ran successfully.\nPASSED\n")
        else:
            error_message = f"Executable returned non-zero exit code: {return_code}"
            error_message += f"\nCommand: {' '.join(command)}"
            error_message += "\nFAILED\n"
            _log_output(log_file, error_message)
            print(error_message)

        # Log peak memory usage
        if check_memory:
            peak_memory_mb = peak_memory / (1024 * 1024)  # Convert bytes to megabytes
            _log_output(log_file, f"Peak memory usage: {peak_memory_mb:.2f} MB\n")
            stats['peak_memory'] = peak_memory_mb

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

    return return_code, stats

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

def _move_log_files(input_log_file, test_name):
    # Move log_file to a unique name with the date and time
    date_time = _get_date_time()
    log_file_base = input_log_file.split('.')[0]
    log_file = log_file_base + '_' + test_name + '_' + date_time + '.log'
    os.rename(input_log_file, log_file)

def _print_pass_fail(test_name, return_code, executable_time, extra_message=None):
    GREEN = '\033[92m'  # Green text
    RED = '\033[91m'   # Red text
    RESET = '\033[0m'  # Reset color
    TEST_NAME_WIDTH = 30
    TIME_WIDTH = 12

    status = f"{GREEN}PASS{RESET}" if return_code == 0 else f"{RED}FAIL{RESET}"
    time_formatted = f"{executable_time:.4e}"
    message = f"message: {extra_message}" if extra_message else ""

    print(f"    {status}:    time(s): {time_formatted:>{TIME_WIDTH}}    test: {test_name:<{TEST_NAME_WIDTH}}{message}")

    if return_code != 0:
        print(f"        Return code: {return_code}")

class RegressionTest:

    def __init__(self, test_name, executable_path, num_procs, exe_args):
        self.test_name = test_name
        self.log_file = 'regression_test.log'
        self.executable_path = executable_path
        self.num_procs = num_procs
        self.exe_args = exe_args
        self.executable_time = 0
        self.peak_memory = 0

    def run(self):
        _remove_file(self.log_file)
        return_code, stats = self._run()
        _print_pass_fail(self.test_name, return_code, self.executable_time)
        _move_log_files(self.log_file, self.test_name)
        return return_code, stats

    def _run(self):
        command_pre = ['mpirun', '-n', str(self.num_procs)]
        # Time the executable
        start_time = time.perf_counter()
        return_code, stats = _run_executable(command_pre, self.executable_path, self.exe_args, self.log_file, check_memory=True)
        self.peak_memory = stats['peak_memory']
        end_time = time.perf_counter()
        self.executable_time = end_time - start_time
        return return_code, stats

class PeakMemoryCheck:

    def __init__(self, test_name, peak_memory, gold_peak_memory, tolerance_percent):
        self.test_name = test_name
        self.peak_memory = peak_memory
        self.gold_peak_memory = gold_peak_memory
        self.tolerance_percent = tolerance_percent / 100.0

    def run(self):
        # Check if the peak memory is within the tolerance
        upper_limit = self.gold_peak_memory * (1.0 + self.tolerance_percent)
        message = f"Peak memory value: {self.peak_memory} MB, Gold value: {self.gold_peak_memory:.2f} MB, Upper limit {upper_limit:.2f} MB"
        return_code = 0
        if self.peak_memory > upper_limit:
            print(f"    Peak memory ({self.peak_memory:.2f} MB) exceeded the gold peak memory ({self.gold_peak_memory:.2f} MB) by more than {self.tolerance_percent*100.0}%")
            return_code = 1
        _print_pass_fail(self.test_name, return_code, 0, message)

        return return_code

class ExodiffCheck:

    def __init__(self, test_name, exodiff_path, exodiff_file, exodiff_results_file, exodiff_gold_results_file, exodiff_args):
        self.test_name = test_name
        self.log_file = 'exodiff_check.log'
        self.exodiff_path = exodiff_path
        self.exodiff_file = exodiff_file
        self.exodiff_results_file = exodiff_results_file
        self.exodiff_gold_results_file = exodiff_gold_results_file
        self.exodiff_args = exodiff_args
        self.executable_time = 0

    def run(self):
        _remove_file(self.log_file)
        return_code = self._run()
        _print_pass_fail(self.test_name, return_code, self.executable_time)
        _move_log_files(self.log_file, self.test_name)
        return return_code

    def _run(self):
        command_pre = []
        # Time the executable
        start_time = time.perf_counter()
        return_code, _stats = _run_executable(command_pre, self.exodiff_path, ['-f', self.exodiff_file, self.exodiff_results_file, self.exodiff_gold_results_file] + self.exodiff_args, self.log_file, check_memory=False)
        end_time = time.perf_counter()
        self.executable_time = end_time - start_time
        return return_code

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
    parser.add_argument('--tolerance_percent', help='Tolerance for peak memory check in percent', default=10)
    parser.add_argument('--peak_memory', help='Peak memory usage in MB. If it is 0, the peak memory check will be skipped.', default=0)
    
    # Parse command line arguments
    return parser.parse_args()

def main():
    # TODO(jake): CLI is not really used so may have issues. Need to test.
    args = _parse_arguments()
    regression_test = RegressionTest(args.name+"_regression_test", args.executable_path, args.num_procs, args.exe_args)
    return_code, stats = regression_test.run()
    if return_code == 0:
        exodiff_test, _stats = ExodiffCheck(args.name+"_exodiff_check", args.exodiff_path, args.exodiff_file, args.exodiff_results_file, args.exodiff_gold_file, args.exodiff_args)
        return_code = exodiff_test.run()

    if return_code == 0 and args.peak_memory != 0:
        memory_test = PeakMemoryCheck(args.name+"_peak_memory_check", stats['peak_memory'], args.peak_memory, args.tolerance_percent)
        return_code = memory_test.run()

    return return_code

if __name__ == "__main__":
    return_code = main()
    exit(return_code)