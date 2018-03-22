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

IF_IMAGE_COLUMNS = [
    'antibody', 'Ab state', 'versions', 'ensembl_ids', 'if_plate_id',
    'position', 'sample', 'filename', 'status', 'locations']


def get_lims_data(path):
    """Return data from xls file."""
    data = pd.read_table(
        path, encoding='ISO-8859-1', header=0, usecols=COLUMNS,
        dtype={
            'Main location': str, 'Other location': str})
    return data


def get_if_images_data(path):
    """Return data from if images csv."""
    data = pd.read_csv(
        path, header=0, usecols=IF_IMAGE_COLUMNS,
        dtype={'versions': str, 'locations': str})
    return data


def get_public(data, public=True):
    """Return public data."""
    if 'versions' in data.columns:
        if public:
            return data[~data['versions'].isnull()]
        return data[data['versions'].isnull()]
    raise ValueError('Data is missing column versions')


def get_filter_mask(data, values):
    """Return boolean mask where dict values matches."""
    return data.isin(values)


def get_cut_mask(data, cut):
    """Return a boolean mask of data size to cut the data in two pieces."""
    return np.random.rand(len(data)) < cut


def get_cut_data(data, cut):
    """Return a two item tuple with data cut according to cut."""
    mask = get_cut_mask(data, cut)
    first = data[mask]
    second = data[~mask]
    return first, second


def get_cell_data(data, cell_lines):
    """Return data where cell line types match cell_lines."""
    return data[get_filter_mask(data['Cell line'], cell_lines)]


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


def exclude_data(data, filter_):
    """Return data where data that matches filter has been removed."""
    return data[~filter_]


def include_data(data, filter_):
    """Return data where only data that matches filter has been included."""
    return data[filter_]


def generate_set(lims_path, if_image_path, plate_range, size, file_list=None):
    """Generate a data set based on criteria.

    Args:
        lims_path : path to statistics csv file.
        if_image_path : path to if image csv file.
        plate_range : integer that filters out plates with lower numbers.
        size : sample size.
        file_list : List of files that should be excluded from the data set.

    Returns:
        Pandas DataFrame filtered on criteria.
    """
    lims_data = get_lims_data(lims_path)
    if_image_data = get_if_images_data(if_image_path)
    if_image_data = get_public(if_image_data)
    # Restrict on plate range.
    plate_range = lims_data['Plate id'] > plate_range
    lims_data = include_data(lims_data, plate_range)
    # Only get data where cell line matches CONTAMINATED_CELLS.
    lims_data = get_cell_data(lims_data, CONTAMINATED_CELLS)
    lims_data = pick_random_data(lims_data, size)
    # Get if image data that is in lims data.
    plate_pos_list = if_image_data['filename'].str.split('_', 2)
    cut_filename = plate_pos_list.apply(lambda s: '_'.join(s[:2]))
    if_image_data = add_column(if_image_data, 'cut_filename', cut_filename)
    paths = get_well_paths(lims_data)
    lims_data = add_column(lims_data, 'cut_filename', paths)
    path_filter = get_filter_mask(
        if_image_data['cut_filename'], lims_data['cut_filename'])
    if_image_data = if_image_data[path_filter]
    if_image_data = add_column(
        if_image_data, 'cell_line', lims_data['Cell line'])
    if file_list:
        if_image_data = if_image_data[
            ~if_image_data['filename'].isin(file_list)]
    return if_image_data


# TODO: Add new name column to data set.
# TODO: Add cell line column to data set. Join data sets on column.
# TODO: Make sure to cut into sample cuts
# after sample filtering on filename and sample size.


if __name__ == '__main__':
    pass
