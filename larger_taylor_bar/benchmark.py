import subprocess
import time
import argparse
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

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

def run_and_plot(executable_path, executable_args, num_runs, baseline, file, live_plot):
    run_times = []

    fig, ax = plt.subplots()
    # Create the run_times np array and fill it with nan
    run_times = np.nan * np.zeros(num_runs)

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
    
    return np.nanmean(run_times) 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run an executable multiple times and plot the run times.')
    parser.add_argument('executable_path', type=str, help='Path to the executable')
    parser.add_argument('executable_args', type=str, help='Arguments to pass to the executable')
    parser.add_argument('--n', type=int, default=10, help='Number of times to run the executable')
    parser.add_argument('--baseline', type=float, default=8.89, help='Baseline run time (seconds)')
    parser.add_argument('--no-plot', dest='plot', action='store_false', default=True, help='Do not plot the run times')
    parser.add_argument('--file', type=str, default='benchmark.pdf', help='File to save the plot to')
    parser.add_argument('--live-plot', dest='live_plot', action='store_true', default=False, help='Live plot the run times')
    args = parser.parse_args()

    average_runtime = 0
    if args.plot:
        average_runtime = run_and_plot(args.executable_path, args.executable_args, args.n, args.baseline, args.file, args.live_plot)
    else:
        average_runtime = run(args.executable_path, args.executable_args, args.n)

    print(f'Average runtime: {average_runtime:.2f} seconds')
