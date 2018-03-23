#!/usr/bin/python3
import click
import csv
import sys
import contextlib
import operator


@contextlib.contextmanager
def smart_open(filename=None):
    if filename and filename != '-':
        file_handle = open(filename, 'w')
    else:
        file_handle = sys.stdout

    try:
        yield file_handle
    finally:
        if file_handle is not sys.stdout:
            file_handle.close()


def cut_csv(csvfile, columns, fieldnames=None, delimiter=',', quotechar='"'):
    """
    Creates a new csvlist containing only the specified columns.
    """
    csvreader = csv.DictReader(csvfile, fieldnames=fieldnames, delimiter=delimiter, quotechar=quotechar)

    include_headers = not fieldnames
    fieldnames = csvreader.fieldnames
    fieldnames = [fieldname for fieldname in fieldnames if fieldname in columns]

    filtered_csv = []
    if include_headers:
        linestring = ''
        for fn in fieldnames:
            if delimiter in fn:
                linestring += '{0}{1}{0}'.format(quotechar, fn) + delimiter
            else:
                linestring += fn + delimiter
        filtered_csv.append(linestring[:-len(delimiter)])

    for line in csvreader:
        linestring = ''
        for fieldname in fieldnames:
            if delimiter in line[fieldname]:
                linestring += '{0}{1}{0}'.format(quotechar, line[fieldname])
                linestring += delimiter
            else:
                linestring += line[fieldname] + delimiter
        linestring.rstrip(delimiter)
        filtered_csv.append(linestring[:-len(delimiter)])
    return filtered_csv


def filter_csv(csvfile, include={}, exclude={}, minimum={}, maximum={},
               fieldnames=None, delimiter=',', quotechar='"',
               strict_min_max_search=False):
    """
    Filters a csv file to include only items containing the correct values in
    the columns.

    The minimum and maximum will compare items based on their values.
    It will first try an float comparison, otherwise a string comparison will
    be used.

    Args:
        csv: The csv file to be filtered.
             Must be a list, file, or file-like object that supports the
             iterator protocol that returns strings as values.
             A column from the csv that contains strings will be considered
             a list delimited by the same delimiter as the columns themselves.
        include: A dictionary with a mapping from csv-header to a list or set
                 of allowed values in the filtered csv.
                 In a column with lists as values, any 1 of the values from the
                 list can match any of the expected values from include.
        exclude: Works oppositely to include. If any value from the csv in the
                 applicable header matches, exclude that item from the returned
                 list.
                 Note that exclude is stronger than include and will remove
                 items that should otherwise have been included.
        minimum: A dictionary with a mapping from csv-header to a list or set
                 of minimum allowed values in the csv.
        maximum: A dictionary with a mapping from csv-header to a list or set
                 of maximum allowed values in the csv.
        fieldnames: A list of headers, to be used if the csv does not have
                    headers of their own.
                    If None, the first row of the csv is presumed to be the
                    header columns.
        delimiter: The delimiter to be used to separate values in the csv.
        quotechar: The character which indicates the start and end of strings
                   (lists).
        strict_min_max_search: By default, min and max search will allow any
                               row that has at least one column element that
                               follows the min-max restriction. If
                               `strict_min_max_search` is enabled, the
                               behaviour will instead be that *every* column
                               element has to follow the restrictions instead.

    Returns:
        A list of strings from csvfile that passed the filters.

    Notes:
        Any column that are not present in any of the parameters is going
        to be ignored and will be included blindly in the output list.

        minimum and maximum comparison are inclusive, i.e. "less/greater than
        or equal to".

    Example usage:
        a_csv = ['a,b', '1,0', '"2,0",0', '5,5', '1,1']
        ret = filter(a_csv, include={'a': {'1', '0'}}, exclude={'b': {'1'}})
        # ret is equal to ['a,b, '1,0', '"2,0",0']
    """
    def filter_line(line, constraints):
        filters = []
        for constraint in constraints:
            constraint_line = line[constraint].split(delimiter)
            constraint_line = [str(value) in constraints[constraint] for value in constraint_line]
            filters.append(any(constraint_line))
        return filters

    def range_limit(line, value_dict, op):
        filters = []
        for constraint, value in value_dict.items():
            constraint_line = line[constraint].split(delimiter)
            try:
                value = float(value)
                constraint_line = [op(float(val), value) for val in constraint_line]
            except ValueError:
                value = str(value)
                constraint_line = [op(str(val), value) for val in constraint_line]

            if strict_min_max_search:
                filters.append(all(constraint_line))
            else:
                filters.append(any(constraint_line))
        return filters

    csvreader = csv.DictReader(csvfile, fieldnames=fieldnames, delimiter=delimiter, quotechar=quotechar)
    filtered_csv = []

    # DictReader removes headers from the read file if we did not supply our own
    # If so, re-add the headers.
    include_headers = not fieldnames
    fieldnames = csvreader.fieldnames

    if include_headers:
        linestring = ''
        for fn in fieldnames:
            if delimiter in fn:
                linestring += '{0}{1}{0}'.format(quotechar, fn) + delimiter
            else:
                linestring += fn + delimiter
        filtered_csv.append(linestring[:-len(delimiter)])

    for line in csvreader:
        if any(filter_line(line, exclude)):
            continue
        if sum(filter_line(line, include)) != len(include):
            continue
        if not all(range_limit(line, minimum, operator.le)):
            continue
        if not all(range_limit(line, maximum, operator.ge)):
            continue

        linestring = ''
        for fieldname in fieldnames:
            if delimiter in line[fieldname]:
                linestring += '{0}{1}{0}'.format(quotechar, line[fieldname])
                linestring += delimiter
            else:
                linestring += line[fieldname] + delimiter
        filtered_csv.append(linestring[:-len(delimiter)])
    return filtered_csv


def validate_argument(context, param, argument):
    try:
        for arg in argument:
            split = arg.split(':')
            if len(split) != 2:
                raise click.BadParameter('Argument must follow the format <a:b>')
        return argument
    except AttributeError:
            raise click.BadParameter('Argument must follow the format <a:b>')


@click.command()
@click.argument('csv_file')
@click.option('-i', '--include', multiple=True, callback=validate_argument,
              help=('Include items matching the parameter.'))
@click.option('-e', '--exclude', multiple=True, callback=validate_argument,
              help=('Exclude items matching the parameter.'))
@click.option('-c', '--columns', help='Only output the specified columns.'
                                      'Needs to be a comma separated list')
@click.option('-o', '--output', default='-', help='Output to a file')
@click.option('--min', multiple=True, callback=validate_argument,
              help='Specify a minimum value for a column')
@click.option('--max', multiple=True, callback=validate_argument,
              help='Specify a maximum value for a column')
@click.option('--strict/--no-strict', default=False,
              help='Use strict min max searching')
def create_dataset(csv_file, include, exclude, columns, output, min, max,
                   strict):
    """
    Creates a dataset from a csv file, including and excluding items from the
    file as required by the user.

    Unless otherwise specified, most arguments should follow
    the format <column name>:<argument>.
    The `column name` should exist in the first row of the IF_file as a column.
    If a row has any item in the specified column matching the argument, they
    will be included or excluded as specified.

    Most arguments can be applied multiple times.
    For example: multiple exclusions can be made by several `-e` arguments.

    By default outputs every available column to stdout.

    Note: Exclusion acts stronger than inclusion.
    """
    include_arguments = {}
    exclude_arguments = {}
    minimum_arguments = {}
    maximum_arguments = {}

    for argument in include:
        argument = argument.split(':')
        include_arguments[argument[0]] = argument[1]

    for argument in exclude:
        argument = argument.split(':')
        exclude_arguments[argument[0]] = argument[1]

    for argument in min:
        argument = argument.split(':')
        minimum_arguments[argument[0]] = argument[1]

    for argument in max:
        argument = argument.split(':')
        maximum_arguments[argument[0]] = argument[1]

    with open(csv_file) as csvfile:
        filtered = filter_csv(csvfile, include_arguments, exclude_arguments,
                              minimum_arguments, maximum_arguments,
                              strict_min_max_search=strict)

    if columns:
        columns = columns.split(',')
        filtered = cut_csv(filtered, columns)

    with smart_open(output) as output_file:
        for filtered_line in filtered:
            output_file.write(filtered_line)
            output_file.write('\n')


if __name__ == '__main__':
    create_dataset()
