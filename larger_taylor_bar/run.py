import sys
sys.path.append('../utils')
import run_test

run_test.run_executable('aperi-mech', 4, ['input.yaml'])
run_test.run_exodiff('exodiff', ['-f', 'compare.exodiff', 'results.exo', 'gold_results.exo'])
