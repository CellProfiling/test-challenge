"""Create final solution csv file."""
import os

import pandas as pd


def create_solution(sol_file, name_file, master_output, safe_output):
    """Create final solution csv file."""
    solution = pd.read_csv(sol_file)
    names = pd.read_csv(
        name_file, sep='\t', header=None, names=['basename', 'new_name'])
    basename = solution['filename'].apply(os.path.basename)
    solution = solution.assign(**{'basename': basename})
    solution.join(names.set_index('basename'), on='basename')
    solution.to_csv(master_output)
    solution = solution[['new_name', 'cell_line']]
    solution = solution.rename(columns={'new_name': 'filename'})
    solution.to_csv(safe_output)
