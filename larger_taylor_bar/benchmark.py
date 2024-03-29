import argparse
import datetime
import os
import platform
import select
import subprocess
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation

def run_once(executable_path, executable_args):
    start_time = time.time()
    subprocess.run([executable_path] + executable_args.split())
    end_time = time.time()
    run_time = end_time - start_time
    return run_time

def run(executable_path, executable_args, num_runs):
    run_times = []

    for i in range(num_runs):
        print(f'Running executable {i+1}/{num_runs}')
        run_time = run_once(executable_path, executable_args)
        run_times.append(run_time)
    
    return np.nanmean(run_times)

def ask_to_set_baseline():
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

def get_baseline():
    # Get the baseline from the runtimes.csv file

    if not os.path.exists('runtimes.csv'):
        # Print a warning if the file does not exist
        print('WARNING: runtimes.csv file not found. Cannot read the baseline runtime.')
        # Ask the user if they want to set the baseline, get the value and return it
        return ask_to_set_baseline()

    df = pd.read_csv('runtimes.csv')

    # Only consider the rows where the platform gold standard is true and it is the same node (machine)
    df = df[(df['Platform Gold Standard'].astype(str).str.lower() == 'true') & (df['Node'] == platform.node())]

    if df.empty:
        # Print a warning if the dataframe is empty
        print('WARNING: No gold standard runtimes found for the current system ' + platform.node() + '. Cannot read the baseline runtime.')
        # Ask the user if they want to set the baseline, get the value and return it
        return ask_to_set_baseline()
    elif df.shape[0] != 1:
        # Print an error if there are multiple rows that match the criteria
        print('WARNING: Multiple gold standard runtimes found for the current system ' + platform.node() + '. Using the last one.')
        # Print the rows that match the criteria, including the row index
        print(df)

    # Find the last row where the platform gold standard is true
    baseline = df.iloc[-1]['Average Runtime (s)']

    return {'value': baseline, 'updated': False}

def run_and_plot(executable_path, executable_args, num_runs, file, live_plot):
    run_times = []

    fig, ax = plt.subplots()
    # Create the run_times np array and fill it with nan
    run_times = np.nan * np.zeros(num_runs)

    # Get the baseline runtime
    baseline_and_updated = get_baseline()
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
        run_time = run_once(executable_path, executable_args)
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

def plot_latest_vs_history(file):
    df = pd.read_csv('runtimes.csv')
    # Sort the DataFrame by date and time
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date')
    # Only consider results from the same machine
    df = df[df['Node'] == platform.node()]

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
    plt.savefig(file)

def add_to_csv(average_runtime):
    columns = ['Date', 'Time', 'Average Runtime (s)', 'Executable Info', 'System', 'Node', 'Release', 'Version', 'Machine', 'Processor', 'Platform Gold Standard']
    # Create the file if it doesn't exist
    if not os.path.exists('runtimes.csv'):
        df = pd.DataFrame(columns=columns)
        df.to_csv('runtimes.csv', index=False)
    elif average_runtime['updated']:
        # Set any rows with the same system and platform gold standard to false
        df = pd.read_csv('runtimes.csv')
        df.loc[(df['System'] == platform.system()) & (df['Platform Gold Standard'].astype(str).str.lower() == 'true'), 'Platform Gold Standard'] = False
        df.to_csv('runtimes.csv', index=False)

    # Date and time
    now = datetime.datetime.now()
    date = now.date()
    now_time = now.time()

    # Machine information
    machine_info = [platform.system(), platform.node(), platform.release(), platform.version(), platform.machine(), platform.processor()]

    # Run --version on the executable
    executable_info = subprocess.run([args.executable_path, '--version'], capture_output=True, text=True).stdout.strip()

    # Create a DataFrame with the new data
    df = pd.DataFrame([[date, now_time, average_runtime['value'], executable_info] + machine_info + [average_runtime['updated']]], columns=columns)

    # Append the new data to the CSV file
    df.to_csv('runtimes.csv', mode='a', header=False, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run an executable multiple times and plot the run times.')
    parser.add_argument('executable_path', type=str, help='Path to the executable')
    parser.add_argument('executable_args', type=str, help='Arguments to pass to the executable')
    parser.add_argument('--n', type=int, default=10, help='Number of times to run the executable')
    parser.add_argument('--no-plot', dest='plot', action='store_false', default=True, help='Do not plot the run times')
    parser.add_argument('--plot-file', type=str, default='benchmark.pdf', help='File to save the plot to')
    parser.add_argument('--history_plot_file', type=str, default='history.pdf', help='File to save the history plot to')
    parser.add_argument('--live-plot', dest='live_plot', action='store_true', default=False, help='Live plot the run times')
    parser.add_argument('--csv', dest='csv', action='store_true', default=False, help='Save the run times to the "runtime.csv" file')
    parser.add_argument('--update-baseline', dest='update_baseline', action='store_true', default=False, help='Update the baseline runtime')
    args = parser.parse_args()

    average_runtime = {0.0, False}
    if args.plot:
        average_runtime = run_and_plot(args.executable_path, args.executable_args, args.n, args.plot_file, args.live_plot)
    else:
        average_runtime = run(args.executable_path, args.executable_args, args.n)

    if args.update_baseline:
        average_runtime['updated'] = True

    if args.csv:
        add_to_csv(average_runtime)

    if args.plot:
        plot_latest_vs_history(args.history_plot_file)

    print(f'Average runtime: {average_runtime["value"]:.2f} seconds')
    if average_runtime['updated']:
        print('The baseline runtime has been updated.')
