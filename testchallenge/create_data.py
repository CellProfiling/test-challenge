"""Module for data parsing."""
import os

import click
import numpy as np
import pandas as pd

PLATE_ID_CUT = 300
CONTAMINATED_CELLS = [
    'U-251 MG', 'HeLa', 'PC-3', 'HEL', 'REH', 'A549', 'MCF-7',
    'U-2 OS', 'HEK 293', 'CACO-2', 'RT4']


def load_data(path):
    """Return data from if images csv."""
    data = pd.read_csv(path, header=0, dtype=str)
    return data


def get_public(data, public=True):
    """Return public data."""
    if 'versions' in data.columns:
        if public:
            return data[~data['versions'].isnull()]
        return data[data['versions'].isnull()]
    raise ValueError('Data is missing column versions')


def get_cut_mask(data, cut):
    """Return a boolean mask of data size to cut the data in two pieces."""
    return np.random.rand(len(data)) < cut


def get_cut_data(data, cut):
    """Return a two item tuple with data cut according to cut."""
    mask = get_cut_mask(data, cut)
    first = data[mask]
    second = data[~mask]
    return first, second


def add_column(data, col_name, column):
    """Return data where a column has been added."""
    return data.assign(**{col_name: column})


def include_columns(data, columns):
    """Return data with only the specified columns."""
    if not isinstance(columns, list):
        columns = [columns]
    return data[columns]


def generate_set(data, exclude, include, maximum, minimum, size=None):
    """Generate a data set based on criteria.

    Args:
        data : DataFrame to filter.
        exclude : Dict of columns and lists of values to exclude.
        include : Dict of columns and lists of values to include.
        maximum : Dict of columns and values that should be max limit.
        minimum : Dict of columns and values that should be min limit.
        size : Sample size.

    Returns:
        Pandas DataFrame filtered on criteria.
    """
    # Exclude items.
    for col, vals in exclude.items():
        data = data[~data[col].isin(vals)]
    # Include items.
    for col, vals in include.items():
        data = data[data[col].isin(vals)]
    # Filter minimum.
    for col, val in minimum.items():
        filt = data[col].astype('float') >= val
        data = data[filt]
    # Filter maximum.
    for col, val in maximum.items():
        filt = data[col].astype('float') <= val
        data = data[filt]
    # Filter randomly on sample size.
    if size and not data.empty:
        data = data.sample(size)
    return data


def generate_all(
        path, cut, exclude=None, include=None, maximum=None, minimum=None,
        size=None, output=None, public=None):
    """Generate all data sets.

    Args:
        path : Path to csv file.
        exclude : Dict of columns and lists of values to exclude.
        include : Dict of columns and lists of values to include.
        maximum : Dict of columns and values that should be max limit.
        minimum : Dict of columns and values that should be min limit.
        size : Sample size.
        public : Boolean where true means only public data should be included.
    """
    if include is None:
        include = {}
    if exclude is None:
        exclude = {}
    if minimum is None:
        minimum = {}
    if maximum is None:
        maximum = {}
    data = load_data(path)
    if public is not None:
        # Filter public/non public.
        data = get_public(data, public=public)
    all_sets = {}
    training = []
    validation = []

    for cell_line in CONTAMINATED_CELLS:
        print(cell_line)
        include['atlas_name'] = [cell_line]
        single_set = generate_set(
            data, exclude, include, maximum, minimum, size)
        single_set = single_set.rename(columns={'atlas_name': 'cell_line'})
        # Split each set 80/20 into training/validation
        cut_data, rest_data = get_cut_data(single_set, cut)
        training.append(cut_data)
        validation.append(rest_data)

    # Combine all training sets and all validation sets into two sets.
    training_set = pd.concat(training)
    validation_set = pd.concat(validation)

    # Sets should have these columns: filename, cell_line.
    for name, part in (
            ('training', training_set), ('validation', validation_set)):
        all_sets[name] = include_columns(part, ['filename', 'cell_line'])

    if output is not None:
        # Save both sets as two csv files.
        for name, data in all_sets.items():
            data.to_csv('{}.csv'.format(
                os.path.join(os.path.normpath(output), name)), index=False)

    return all_sets


@click.group()
def cli():
    """Start CLI."""
    pass


@cli.command()
@click.argument('csv_file')
@click.option('-o', '--output', help='Output to a directory')
def create(csv_file, output):
    """Run script."""
    exclude = None  # add filelist here if needed
    include = None
    maximum = None
    minimum = {'if_plate_id': PLATE_ID_CUT}

    # For each cell line, make a set of sample size 200.
    all_sets = generate_all(
        csv_file, 0.8, exclude, include, maximum, minimum, 200, output=output,
        public=None)

    return all_sets


# TODO: Validate that all paths from one well are in one of the dataset cuts:
# training, validation or test
# TODO: Make sure to cut into sample cuts
# after sample filtering on filename and sample size.

if __name__ == '__main__':
    cli()
