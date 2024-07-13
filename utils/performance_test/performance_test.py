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
    return_code = regression_test.run()
    if return_code != 0:
        print("\033[91mFAIL\033[0m")
        sys.exit(1)
    return regression_test.executable_time

def run(test_name, executable_path, num_procs, executable_args, num_runs, no_ask=False):
    run_times = []

    baseline_and_updated = get_baseline(runtime_file, no_ask)
    updated = baseline_and_updated['updated']

    for i in range(num_runs):
        print(f'Running executable {i+1}/{num_runs}')
        run_time = run_once(test_name, executable_path, num_procs, executable_args)
        run_times.append(run_time)
    
    return {'value': np.nanmean(run_times), 'updated': updated}

def ask_to_set_baseline(no_ask=False):
    if no_ask:
        return {'value': 0.0, 'updated': True}
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
        return {'value': 0.0, 'updated': True}

    print('Not setting the baseline runtime.')
    return {'value': 0.0, 'updated': False}

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
    baseline = df.iloc[-1]['Average Runtime (s)']

    return {'value': baseline, 'updated': False}

def run_and_plot(test_name, executable_path, runtime_file, num_procs, executable_args, num_runs, file, live_plot, no_ask=False):
    run_times = []

    fig, ax = plt.subplots()
    # Create the run_times np array and fill it with nan
    run_times = np.nan * np.zeros(num_runs)

    # Get the baseline runtime
    baseline_and_updated = get_baseline(runtime_file, no_ask)
    baseline = baseline_and_updated['value']
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
        run_time = run_once(test_name, executable_path, num_procs, executable_args)
        run_times[frame] = run_time
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
    
    return {'value': np.nanmean(run_times), 'updated': updated}

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
    columns = ['Date', 'Time', 'Average Runtime (s)', 'Executable Info', 'Release', 'Version', 'Machine', 'Platform Gold Standard']
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
    df = pd.DataFrame([[date, now_time, average_runtime['value'], executable_info] + machine_info + [average_runtime['updated']]], columns=columns)

    # Append the new data to the CSV file
    df.to_csv(runtime_file, mode='a', header=False, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run an executable multiple times and plot the run times.')
    parser.add_argument('executable_path', type=str, help='Path to the executable')
    parser.add_argument('executable_args', type=str, nargs='+', help='Arguments to pass to the executable')
    parser.add_argument('--n', type=int, default=10, help='Number of times to run the executable')
    parser.add_argument('--np', type=int, default=1, help='Number of processors to run the executable with')
    parser.add_argument('--tolerance', type=float, default=3.0, help='Tolerance for the percentage difference')
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

    average_runtime = {0.0, False}
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

    baseline = get_baseline(runtime_file, args.no_ask)['value']
    print(f'Average runtime:  {average_runtime["value"]:.2f} seconds')

    if average_runtime['updated']:
        print('The baseline runtime has been updated.')
        print("\033[92mPASS\033[0m")
        sys.exit(0)
    else:
        percentage_difference = ((average_runtime['value'] - baseline) / baseline) * 100
        print(f'Baseline runtime: {baseline:.2f} seconds')
        print(f'Percentage difference: {percentage_difference:.2f}%')
        if abs(percentage_difference) > args.tolerance:
            print(f'The percentage difference is greater than the tolerance of {args.tolerance}.')
            print(f'Acceptable range: [{baseline*(1-args.tolerance/100.0):.2f}, {baseline*(1+args.tolerance/100.0):.2f}]')
            print ("\033[91mFAIL\033[0m")
            sys.exit(1)
        else:
            print(f'The percentage difference is within the tolerance of {args.tolerance}.')
            print(f'Acceptable range: [{baseline*(1-args.tolerance/100.0):.2f}, {baseline*(1+args.tolerance/100.0):.2f}]')
            print("\033[92mPASS\033[0m")
            sys.exit(0)
