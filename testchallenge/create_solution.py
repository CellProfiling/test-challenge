"""Create final solution csv file."""
import os

import click
import pandas as pd


@click.group()
def cli():
    """Start CLI."""
    pass


@cli.command()
@click.option('-s', '--solution', help='Solution file.')
@click.option('-t', '--translation', help='Translation file.')
@click.option('-m', '--master', help='Master output file with all info.')
@click.option('-u', '--upload', help='File to be uploaded for scoring.')
def create_solution(solution, translation, master_output, safe_output):
    """Create final solution csv file."""
    solution = pd.read_csv(solution)
    translation = pd.read_csv(
        translation, sep='\t', header=None, names=['basename', 'new_name'])
    basename = solution['filename'].apply(os.path.basename)
    solution = solution.assign(**{'basename': basename})
    solution.join(translation.set_index('basename'), on='basename')
    solution.to_csv(master_output)
    solution = solution[['new_name', 'cell_line']]
    solution = solution.rename(columns={'new_name': 'filename'})
    solution.to_csv(safe_output)


if __name__ == '__main__':
    cli()
