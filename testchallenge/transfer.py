"""Functions for transferring files."""
import csv
import re
import shutil
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


@cli.command()
@click.option(
    '-r', '--root', required=True,
    type=click.Path(exists=True, file_okay=False))
@click.option(
    '-d', '--dest', required=True,
    type=click.Path(exists=True, file_okay=False, writable=True))
@click.option('-f', '--files', required=True, type=click.Path(exists=True))
@click.option('-e', '--exclude', required=True, type=click.STRING)
@click.option('-i', '--include', required=True, type=click.STRING)
def copy(root, dest, files, exclude, include):
    """Copy files matching include pattern but not exclude pattern."""
    file_list = load_csv(files)
    for path in file_list:
        path = Path(root).joinpath(path.strip('/'))
        filename = path.name
        glob_paths = path.parent.glob(filename + include)
        path_list = [
            path for path in glob_paths if not re.search(exclude, path.name)]
        if not path_list:
            print('No files found')
            return
        for path_ in path_list:
            new_path = shutil.copy(path_, dest)
            print('Copied: ', path_)
            print('Destination: ', new_path)


if __name__ == '__main__':
    cli()
