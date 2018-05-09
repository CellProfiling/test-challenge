"""Module for data parsing."""
import os

import click
import pandas as pd
from sklearn.model_selection import train_test_split

PLATE_ID_CUT = 300
CONTAMINATED_CELLS = [
    'U-251 MG', 'HeLa', 'PC-3', 'A549', 'MCF7',
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


def add_column(data, col_name, column):
    """Return data where a column has been added."""
    return data.assign(**{col_name: column})


def include_columns(data, columns):
    """Return data with only the specified columns."""
    if not isinstance(columns, list):
        columns = [columns]
    return data[columns]


def generate_set(data, exclude, include, maximum, minimum):
    """Generate a data set based on criteria.

    Args:
        data : DataFrame to filter.
        exclude : Dict of columns and lists of values to exclude.
        include : Dict of columns and lists of values to include.
        maximum : Dict of columns and values that should be max limit.
        minimum : Dict of columns and values that should be min limit.

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
    return data


def generate_all(
        path, cut, exclude=None, include=None, maximum=None, minimum=None,
        size=None, output=None, public=None):
    """Generate all data sets.

    Args:
        path : Path to csv file.
        cut : Float 0..1 representing how to cut training and validation.
        exclude : Dict of columns and lists of values to exclude.
        include : Dict of columns and lists of values to include.
        maximum : Dict of columns and values that should be max limit.
        minimum : Dict of columns and values that should be min limit.
        size : Sample size.
        output : Path to directory where to save csv files with data.
        public : Boolean where true means only public data should be included.

    Returns:
        Dict with two Pandas DataFrame for training and validation.

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
    data = data.rename(columns={'atlas_name': 'cell_line'})
    if public is not None:
        # Filter public/non public.
        data = get_public(data, public=public)
    training = []
    validation = []

    for cell_line in CONTAMINATED_CELLS:
        include['cell_line'] = [cell_line]
        single_set = generate_set(data, exclude, include, maximum, minimum)
        # Add a column with well path based on column filename.
        well_path = single_set['filename'].str.replace(r'_\d+_', '')
        single_set = add_column(single_set, 'well_path', well_path)
        # Drop duplicates on well path.
        single_set = single_set.drop_duplicates('well_path')
        # Filter randomly on sample size.
        if size and not single_set.empty:
            single_set = single_set.sample(size)
        # Sets should have these columns: filename, cell_line.
        single_set = include_columns(single_set, ['filename', 'cell_line'])
        # Split each set 80/20 into training/validation
        training_cut, validation_cut = train_test_split(
            single_set, test_size=1 - cut)
        print('Cell line: {:>8}, training: {}, validation: {}'.format(
            cell_line, len(training_cut), len(validation_cut)))
        training.append(training_cut)
        validation.append(validation_cut)

    # Combine all training sets and all validation sets into two sets.
    training = pd.concat(training)
    validation = pd.concat(validation)

    if output is not None:
        # Save both sets as two csv files.
        for name, data in ('training', training), ('validation', validation):
            data.to_csv('{}.csv'.format(
                os.path.join(os.path.normpath(output), name)), index=False)

    return {'training': training, 'validation': validation}


@click.group()
def cli():
    """Start CLI."""
    pass


@cli.command()
@click.argument('csv_file')
@click.option('-o', '--output', help='Output to a directory')
def create(csv_file, output=None):
    """Run script."""
    exclude = None  # add filelist here if needed
    include = None
    maximum = None
    minimum = {'if_plate_id': PLATE_ID_CUT}

    # For each cell line, make a set of sample size 200.
    all_sets = generate_all(
        csv_file, 0.8, exclude, include, maximum, minimum, 100, output=output,
        public=True)

    return all_sets


if __name__ == '__main__':
    cli()
