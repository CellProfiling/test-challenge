"""Module for data parsing."""
import os

import pandas as pd
import numpy as np


IN_ATLAS = 'In atlas 18.0'
PLATE_ID_CUT = 300
COLUMNS = [
    'Antibody', 'IH state', 'Antibody state', IN_ATLAS,
    'Ensembl id', 'Cell line', 'Plate id', 'Position',
    'Main location', 'Other location']
CONTAMINATED_CELLS = [
    'U-251 MG', 'HeLa', 'PC-3', 'HEL', 'REH', 'A549', 'MCF-7',
    'U-2 OS', 'HEK 293', 'CACO-2', 'RT4']


def get_data(path):
    """Return data from xls file."""
    def conv_location(_string):
        """Split on comma."""
        _string.split(',')

    data = pd.read_table(
        path, encoding='ISO-8859-1', header=0, usecols=COLUMNS,
        converters={
            'Main location': conv_location, 'Other location': conv_location})
    return data


TEST = get_data('Confocal_data_finished_antibodies_2018-02-21.xls')


def get_public(data, public=True):
    """Return public data."""
    if public:
        public = 'Yes'
    else:
        public = 'No'
    return data[data[IN_ATLAS] == public]


get_public(TEST)


def get_filter_mask(data, col_name, _filter):
    """Return boolean mask where values of col_name is in filter."""
    return data[col_name].isin(_filter)


def get_cut_mask(data, cut):
    """Return a boolean mask of data size to cut the data in two pieces."""
    return np.random.rand(len(data)) < cut


def get_cell_data(data, cell_lines):
    """Return data where cell line types match cell_lines."""
    return data[get_filter_mask(data, 'Cell line', cell_lines)]


get_cell_data(TEST, CONTAMINATED_CELLS)


def get_well_paths(data):
    """Return a Pandas series with paths to images in data."""
    return (data['Plate id'].map(lambda x: os.path.join('/archive', str(x))) +
            '/' + data['Plate id'].map(str) + '_' + data['Position'])


def add_column(data, col_name, column):
    """Return data where a column has been added."""
    return data.assign(**{col_name: column})


def pick_random_data(data, number_rows):
    """Return randomly selected specified number of rows of data."""
    return data.sample(number_rows)


pick_random_data(TEST, 2)


if __name__ == '__main__':
    pass
