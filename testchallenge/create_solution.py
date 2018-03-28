"""Create final solution csv file."""
import os

import click
import pandas as pd


@click.group()
def cli():
    """Start CLI."""
    pass


@cli.command()
@click.option(
    '-s', '--solution', type=click.Path(exists=True, dir_okay=False),
    help='Solution file.')
@click.option(
    '-t', '--translation', type=click.Path(exists=True, dir_okay=False),
    help='Translation file.')
@click.option(
    '-m', '--master', type=click.Path(dir_okay=False, writable=True),
    help='Master output file with all info.')
@click.option(
    '-u', '--upload', type=click.Path(dir_okay=False, writable=True),
    help='File to be uploaded for scoring.')
def create_solution(solution, translation, master, upload):
    """Create final solution csv file."""
    solution = pd.read_csv(solution)
    translation = pd.read_csv(
        translation, sep='\t', header=None, names=['basename', 'new_name'])
    basename = solution['filename'].apply(os.path.basename)
    solution = solution.assign(**{'basename': basename})
    solution = solution.join(translation.set_index('basename'), on='basename')
    solution.to_csv(master, index=False)
    solution = solution[['new_name', 'cell_line']]
    solution = solution.rename(columns={'new_name': 'filename'})
    solution = solution.sort_values(by=['filename'])
    solution.to_csv(upload, index=False)


if __name__ == '__main__':
    cli()
