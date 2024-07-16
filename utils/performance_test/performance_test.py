import argparse
import datetime
import os
import platform
import select
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation
import sys
# script directory
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_dir+os.sep+'..')
from regression_test import RegressionTest

def run_once(test_name, executable_path, num_procs, executable_args):
    regression_test = RegressionTest(test_name, executable_path, num_procs, executable_args)
    return_code, stats = regression_test.run()
    if return_code != 0:
        print("\033[91mFAIL\033[0m")
        sys.exit(1)
    return regression_test.executable_time, stats['peak_memory']

def run(test_name, executable_path, num_procs, executable_args, num_runs, no_ask=False):
    run_times = []
    peak_memory_values = []

    baseline_and_updated = get_baseline(runtime_file, no_ask)
    updated = baseline_and_updated['updated']

    for i in range(num_runs):
        print(f'Running executable {i+1}/{num_runs}')
        run_time, peak_memory = run_once(test_name, executable_path, num_procs, executable_args)
        peak_memory_values.append(peak_memory)
        run_times.append(run_time)
    
    return {'time': np.nanmean(run_times), 'updated': updated, 'peak_memory': np.nanmean(peak_memory_values)}

def ask_to_set_baseline(no_ask=False):
    if no_ask:
        return {'time': 0.0, 'updated': True, 'peak_memory': 0.0}
    set_baseline = False

    # Ask the user if they want to set the baseline
    print('Would you like to set the baseline for the current system?')

    # Wait for 10 seconds for the user to respond, then return False
    print('Enter "yes" or "no" (automatically selecting "no" in 10 seconds):\n', end='\r')
    i, o, e = select.select([sys.stdin], [], [], 10)
    if (i):
        answer = sys.stdin.readline().strip()
        if answer[0].lower() == 'y':
            set_baseline = True
        elif answer[0].lower() == 'n':
            set_baseline = False
        else:
            print('Invalid input. Please enter "yes" or "no".')
    else:
        print('No input received, automatically selecting "no".')

    if set_baseline:
        print('Setting the baseline runtime.')
        return {'time': 0.0, 'updated': True, 'peak_memory': 0.0}

    print('Not setting the baseline runtime.')
    return {'time': 0.0, 'updated': False, 'peak_memory': 0.0}

def get_baseline(runtime_file, no_ask=False):
    # Get the baseline from the runtime file

    if not os.path.exists(runtime_file):
        # Print a warning if the file does not exist
        print(f'WARNING: {runtime_file} file not found. Cannot read the baseline runtime.')
        # Ask the user if they want to set the baseline, get the value and return it
        return ask_to_set_baseline(no_ask)

    df = pd.read_csv(runtime_file)

    # Only consider the rows where the platform gold standard is true
    df = df[(df['Platform Gold Standard'].astype(str).str.lower() == 'true')]

    if df.empty:
        # Print a warning if the dataframe is empty
        print('WARNING: No gold standard runtimes found for the current system ' + platform.node() + '. Cannot read the baseline runtime.')
        # Ask the user if they want to set the baseline, get the value and return it
        return ask_to_set_baseline(no_ask)
    elif df.shape[0] != 1:
        # Print an error if there are multiple rows that match the criteria
        print('WARNING: Multiple gold standard runtimes found for the current system ' + platform.node() + '. Using the last one.')
        # Print the rows that match the criteria, including the row index
        print(df)

    # Find the last row where the platform gold standard is true
    baseline_runtime = df.iloc[-1]['Average Runtime (s)']
    baseline_peak_memory = df.iloc[-1]['Peak Memory (MB)']

    return {'time': baseline_runtime, 'updated': False, 'peak_memory': baseline_peak_memory}

def run_and_plot(test_name, executable_path, runtime_file, num_procs, executable_args, num_runs, file, live_plot, no_ask=False):
    run_times = []

    fig, ax = plt.subplots()
    # Create the run_times and peak_memory np array and fill it with nan
    run_times = np.nan * np.zeros(num_runs)
    peak_memory_values = np.nan * np.zeros(num_runs)

    # Get the baseline runtime
    baseline_and_updated = get_baseline(runtime_file, no_ask)
    baseline = baseline_and_updated['time']
    updated = baseline_and_updated['updated']

    def init():
        ax.plot([0.875, num_runs+0.125], [baseline, baseline], 'k--', label='Baseline = {:.2f}s'.format(baseline))
        ax.set_xlabel('Run')
        ax.set_ylabel('Run Time (seconds)')
        ax.set_xlim(0.75, num_runs + 0.25)
        ax.legend()
        ax.set_title(f'Execution Time of Executable\nBaseline: {baseline:.2f} seconds')
        plt.tight_layout()
        return ax

    def update(frame):
        print(f'Running executable {frame+1}/{num_runs}')
        run_time, peak_memory = run_once(test_name, executable_path, num_procs, executable_args)
        run_times[frame] = run_time
        peak_memory_values[frame] = peak_memory
        ax.clear()
        # Make each run be a bar, width 0.25
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='black', alpha=0.7)
        ax.bar(range(1,run_times.shape[0]+1), run_times, width=0.25, label='Runs', zorder=2)
        # Add text to each bar
        for i, run_time in enumerate(run_times):
            if run_time == np.nan: continue
            ax.text(i+1, run_time, f'{run_time:.2f}', ha='center', va='bottom')
        # Calculate the average, ignore nan values
        average = np.nanmean(run_times)
        ax.plot([0.875, num_runs+0.125], [average, average], 'k-', label='Average = {:.2f}s'.format(average))
        ax.plot([0.875, num_runs+0.125], [baseline, baseline], 'k--', label='Baseline = {:.2f}s'.format(baseline))
        ax.set_xlabel('Run')
        ax.set_ylabel('Run Time (seconds)')
        ax.legend()
        # Calculate the percentage difference and print it
        percentage_difference = ((average - baseline) / baseline) * 100
        ax.set_title(f'Execution Time of Executable\nAverage: {average:.2f} seconds, {percentage_difference:.2f}% difference from baseline')
        plt.tight_layout()

    if live_plot:
        ani = FuncAnimation(fig, update, frames=range(num_runs), repeat=False, init_func=init)
        ani.event_source.add_callback(lambda: plt.savefig(file))
        plt.show()
    else:
        for frame in range(num_runs):
            update(frame)
        plt.savefig(file)
    
    return {'time': np.nanmean(run_times), 'updated': updated, 'peak_memory': np.nanmean(peak_memory_values)}

def plot_latest_vs_history(runtime_file, plot_file):
    df = pd.read_csv(runtime_file)
    # Sort the DataFrame by date and time
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date')

    # Grab the last gold standard run time
    df_gold = df[df['Platform Gold Standard'].astype(str).str.lower() == 'true']

    fig, ax = plt.subplots()
    # The last one is the latest run
    ax.plot(df.iloc[-1]['Date'], df.iloc[-1]['Average Runtime (s)'], 'ro', label='Latest')
    ax.plot(df['Date'], df['Average Runtime (s)'], 'k--', label='History')
    ax.plot(df_gold['Date'], df_gold['Average Runtime (s)'], 'gx', label='Gold Standard')

    ax.set_xlabel('Date')
    ax.set_ylabel('Runtime (seconds)')
    ax.set_title('Latest, Gold Standard, and Historical Runtimes')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(plot_file)

def add_to_csv(runtime_file, average_runtime):
    columns = ['Date', 'Time', 'Average Runtime (s)', 'Peak Memory (MB)', 'Executable Info', 'Release', 'Version', 'Machine', 'Platform Gold Standard']
    # Create the file if it doesn't exist
    if not os.path.exists(runtime_file):
        df = pd.DataFrame(columns=columns)
        df.to_csv(runtime_file, index=False)
    elif average_runtime['updated']:
        # Set any rows with the same platform gold standard to false
        df = pd.read_csv(runtime_file)
        df.loc[(df['Platform Gold Standard'].astype(str).str.lower() == 'true'), 'Platform Gold Standard'] = False
        df.to_csv(runtime_file, index=False)

    # Date and time
    now = datetime.datetime.now()
    date = now.date()
    now_time = now.time()

    # Machine information
    machine_info = [platform.release(), platform.version(), platform.processor()]

    # Run --version on the executable
    executable_info = subprocess.run([args.executable_path, '--version'], capture_output=True, text=True).stdout.strip()

    # Create a DataFrame with the new data
    df = pd.DataFrame([[date, now_time, average_runtime['time'], average_runtime['peak_memory'], executable_info] + machine_info + [average_runtime['updated']]], columns=columns)

    # Append the new data to the CSV file
    df.to_csv(runtime_file, mode='a', header=False, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run an executable multiple times and plot the run times.')
    parser.add_argument('executable_path', type=str, help='Path to the executable')
    parser.add_argument('executable_args', type=str, nargs='+', help='Arguments to pass to the executable')
    parser.add_argument('--n', type=int, default=10, help='Number of times to run the executable')
    parser.add_argument('--np', type=int, default=1, help='Number of processors to run the executable with')
    parser.add_argument('--time-tolerance', type=float, default=3.0, help='Tolerance for the percentage difference in run time')
    parser.add_argument('--memory-tolerance', type=float, default=3.0, help='Tolerance for the percentage difference in peak memory')
    parser.add_argument('--no-plot', dest='plot', action='store_false', default=True, help='Do not plot the run times')
    parser.add_argument('--live-plot', dest='live_plot', action='store_true', default=False, help='Live plot the run times')
    parser.add_argument('--csv', dest='csv', action='store_true', default=False, help='Save the run times to the "runtime.csv" file')
    parser.add_argument('--update-baseline', dest='update_baseline', action='store_true', default=False, help='Update the baseline runtime')
    parser.add_argument('--no-ask', dest='no_ask', action='store_true', default=False, help='Set the baseline if it does not exist without asking')
    args = parser.parse_args()

    machine_info = [platform.node(), platform.system(), platform.processor()]

    test_name = '_'.join(machine_info) + '_' + '_'.join(args.executable_path.split(os.sep)[-2:]) + '_num_procs_' + str(args.np)
    runtime_file = 'runtime_' + test_name + '.csv'
    plot_file = 'benchmark_' + test_name + '.png'
    history_plot_file = 'history_' + test_name + '.png'

    average_runtime = {0.0, False, 0.0}
    if args.plot:
        average_runtime = run_and_plot(test_name, args.executable_path, runtime_file, args.np, args.executable_args, args.n, plot_file, args.live_plot, args.no_ask)
    else:
        average_runtime = run(test_name, args.executable_path, args.np, args.executable_args, args.n, args.no_ask)

    if args.update_baseline:
        average_runtime['updated'] = True

    if args.csv or average_runtime['updated']:
        add_to_csv(runtime_file, average_runtime)

    if args.plot:
        plot_latest_vs_history(runtime_file, history_plot_file)

    baseline = get_baseline(runtime_file, args.no_ask)
    baseline_runtime = baseline['time']
    baseline_memory = baseline['peak_memory']
    print(f'Average runtime:  {average_runtime["time"]:.2f} seconds')
    print(f'Peak memory: {average_runtime["peak_memory"]:.2f} MB')

    if average_runtime['updated']:
        print('The baseline runtime and peak memory have been updated.')
        print("\033[92mPASS\033[0m")
        sys.exit(0)
    else:
        # Check if the average runtime is within the tolerance
        percentage_difference = ((average_runtime['time'] - baseline_runtime) / baseline_runtime) * 100
        print(f'Baseline runtime: {baseline_runtime:.2f} seconds')
        print(f'Percentage difference: {percentage_difference:.2f}%')
        return_code = 0
        if abs(percentage_difference) > args.time_tolerance:
            print(f'The percentage difference is greater than the tolerance of {args.time_tolerance}.')
            print(f'Acceptable range: [{baseline_runtime*(1-args.time_tolerance/100.0):.2f}, {baseline_runtime*(1+args.time_tolerance/100.0):.2f}]')
            print ("\033[91mFAIL\033[0m")
            return_code = 1
        else:
            print(f'The percentage difference is within the tolerance of {args.time_tolerance}.')
            print(f'Acceptable range: [{baseline_runtime*(1-args.time_tolerance/100.0):.2f}, {baseline_runtime*(1+args.time_tolerance/100.0):.2f}]')
            print("\033[92mPASS\033[0m")

        # Check if the peak memory is within the tolerance
        upper_limit = baseline_memory * (1.0 + args.memory_tolerance / 100.0)
        if average_runtime['peak_memory'] > upper_limit:
            print(f"Peak memory ({average_runtime['peak_memory']:.2f} MB) exceeded the gold peak memory ({baseline_memory:.2f} MB) by more than {args.memory_tolerance}%")
            print(f"Upper limit: {upper_limit:.2f} MB")
            print("\033[91mFAIL\033[0m")
            return_code = 1
        else:
            print(f"Peak memory ({average_runtime['peak_memory']:.2f} MB) is within the tolerance of {args.memory_tolerance}% of the gold peak memory ({baseline_memory:.2f} MB)")
            print(f"Upper limit: {upper_limit:.2f} MB")
            print("\033[92mPASS\033[0m")
        sys.exit(return_code)
