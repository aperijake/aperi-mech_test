import argparse
import subprocess

def parse_arguments():
    # Define command line arguments
    parser = argparse.ArgumentParser(description='Run an executable and check its return value.')
    parser.add_argument('-n', '--num_procs', help='Number of processors for running the executable', default=1)
    parser.add_argument('-p', '--executable_path', help='Path to the executable', default='aperi-mech')
    parser.add_argument('-d', '--exodiff_path', help='Path to exodiff', default='exodiff')
    parser.add_argument('-f', '--exodiff_file', help='Path to exodiff file.', default='compare.exodiff')
    parser.add_argument('--exe_args', nargs='*', help='Additional arguments to pass to the executable')
    parser.add_argument('--exodiff_args', nargs='*', help='Additional arguments to pass to exodiff')
    
    # Parse command line arguments
    return parser.parse_args()


def _run_executable(command_pre, executable_path, args):
    try:
        # Run the executable with additional arguments
        command = command_pre + [executable_path] + args
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for the process to finish and get the return code
        return_code = process.wait()
        
        # Check the return code
        if return_code == 0:
            print("Executable ran successfully.")
        else:
            print(f"Executable returned non-zero exit code: {return_code}")
        
        # Capture stdout and stderr
        stdout, stderr = process.communicate()
        if stdout:
            print("Standard output:")
            print(stdout.decode())
        if stderr:
            print("Standard error:")
            print(stderr.decode())
    
    except FileNotFoundError:
        print(f"Executable not found at path: {executable_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def run_executable(executable_path, num_procs, args):
    command_pre = ['mpirun', '-n', str(num_procs)]
    _run_executable(command_pre, executable_path, args)

def run_exodiff(exodiff_path, args):
    _run_executable([], exodiff_path, args)

def main():
    args = parse_arguments()
    run_executable(args.executable_path, args.num_procs, args.exe_args)
    run_exodiff(args.exodiff_path, ['-f', args.exodiff_file] + args.exodiff_args)

if __name__ == "__main__":
    main()

