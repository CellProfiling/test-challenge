"""Functions for transferring files."""
import csv
import shutil
import sys
from pathlib import Path

import click

ARCHIVE_PATH = '/archive'


@click.group()
def cli():
    """Copy files that match pattern."""
    pass


def load_csv(path):
    """Load csv file."""
    files = []
    with open(path) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if not row[0].startswith(ARCHIVE_PATH):
                continue
            files.append(row[0])
    return files


@cli.command(name='copy')
@click.option(
    '-r', '--root', required=True,
    type=click.Path(exists=True, file_okay=False))
@click.option(
    '-d', '--dest', required=True,
    type=click.Path(exists=True, file_okay=False, writable=True))
@click.option('-f', '--files', required=True, type=click.Path(exists=True))
@click.option('-p', '--pattern', required=True, type=click.STRING)
def copy(root, dest, files, pattern):
    """Copy files matching pattern."""
    file_list = load_csv(files)
    for path in file_list:
        path = Path(root).joinpath(path.strip('/'))
        filename = path.name
        glob_paths = path.parent.glob(filename + pattern)
        path_list = list(glob_paths)
        if not path_list:
            print('No files found')
            sys.exit(1)
        for path_ in path_list:
            new_path = shutil.copy(path_, dest)
            print('Copied: ', path_)
            print('Destination: ', new_path)


if __name__ == '__main__':
    cli()
