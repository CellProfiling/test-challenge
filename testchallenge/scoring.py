#!/usr/bin/python3
"""Handle scoring of predictions."""
import argparse
import collections
import csv
import sys

import numpy as np
import simplejson


def precision_recall(prediction, actual, include_f1=False, mode='total'):
    """Calculate the precision and recall for a prediction on a dataset.

    Optionally calculate the f1 score as well.

    Args:
        prediction: A binary matrix representing the predictions on the
            dataset.
        actual: A binary matrix representing the actual true positives
            of the dataset.
        include_f1: Whether or not to include f1 in the return values.
        mode: One of 'total' or 'class'.
              In 'total' mode, the entire set is considered.
              In 'class' mode, the precision and recall is calculated
              for each class individually.
    Returns:
        A tuple containing (precision, recall).
        If include_f1 is True, the tuple contains (precision, recall, f1).
    """
    if mode == 'total':
        axis = None
    elif mode == 'class':
        axis = 0
    else:
        raise ValueError('The mode has to be either "total" or "class"')

    truepos = np.logical_and(prediction, actual)
    false = np.subtract(actual, prediction)
    falsepos = false < 0
    falseneg = false > 0

    truepos = np.sum(truepos, axis=axis)
    falsepos = np.sum(falsepos, axis=axis)
    falseneg = np.sum(falseneg, axis=axis)

    with np.errstate(divide='ignore', invalid='ignore'):
        precision = truepos / (truepos + falsepos)
        recall = truepos / (truepos + falseneg)
        if not np.isscalar(precision):
            precision[~np.isfinite(precision)] = 0
            recall[~np.isfinite(recall)] = 0

        if include_f1:
            f1_score = 2 * (precision * recall) / (precision + recall)

    if include_f1:
        return precision, recall, f1_score
    return precision, recall


def jaccard_index(y_true, y_predict):
    """Calculate the Jaccard index of the predictions on the true values.

    Also known as Jaccard similarity, Hamming score, or multi-label accuracy.

    Defined as:
    Let y_true=T, and y_predict=S.
    The Jaccard index  is calculated as
    |intersection(T,S)|/|union(T,S)|

    Args:
        y_true:   A list of binary vectors.
                  The list should consist of the target vectors.

        y_predict:   A list of binary vectors.
                     The list should consist of the prediction vectors.
    Returns:
        The Jaccard index (jaccard similarity) of the predictions
        on the true labels.
    """
    numerator = 0
    denominator = 0
    for (true_item, pred_item) in zip(y_true, y_predict):
        if len(true_item) != len(pred_item):
            raise ValueError('Array lengths do not agree')

        true = set(np.where(true_item)[0])
        pred = set(np.where(pred_item)[0])

        intersection = true.intersection(pred)
        union = true.union(pred)
        numerator += len(intersection)
        denominator += len(union)
    return numerator / denominator


class Binarizer(object):
    """A binarizer where 1 means class is present, 0 means it is not."""

    def __init__(self, classes):
        """Args:
            classes: A list of the classes that can be binarized.
        """
        self.classes = sorted(set(classes))
        self._index = dict(zip(self.classes, range(len(self.classes))))
        self._reverse_index = dict(zip(range(len(self.classes)), self.classes))

    def bin_label(self, item):
        """Binarize a single item.

        If the item is iterable and is not a string, the item will be
        binarized as a multi-label item.
        """
        bin_ = [0] * len(self.classes)
        if (isinstance(item, collections.Iterable) and
                not isinstance(item, str)):
            for class_ in item:
                bin_[self._index[class_]] = 1
        else:
            bin_[self._index[item]] = 1
        return bin_

    def binarize(self, to_bin):
        """Binarize a list of labels.

        Args:
            to_bin: A list of of labels to be binarized.
               Items in `to_bin` that are iterable (except strings)
               will be binarized as a multi-label item. All other items
               will be binarized as a single-label item.
        Returns:
            A list of binarized label lists.
        """
        binarized = []
        for item in to_bin:
            bin_ = self.bin_label(item)
            binarized.append(bin_)
        return binarized

    def unbin_label(self, item):
        """Unbinarize a single item."""
        unbin = []
        for idx in item:
            if idx:
                unbin.append(self._reverse_index[idx])
        return unbin

    def unbinarize(self, from_bin):
        """Unbinarize a list of binarized labels."""
        unbinarized = []
        for item in from_bin:
            unbinarized.append(self.unbin_label(item))
        return unbinarized

    def __iter__(self):
        return self.classes

    def __len__(self):
        return len(self.classes)

    __call__ = binarize


def parse_solution_file(solution_file):
    """Parse a solution file."""
    ids = []
    classes = []
    with open(solution_file) as file_handle:
        solution_reader = csv.reader(file_handle)
        header = next(solution_reader, None)
        if header != HEADER:
            raise ValueError(
                'Incorrect header found: {}, should be: {}'.format(
                    header, HEADER))
        for row in solution_reader:
            if len(row) < 2:
                raise ValueError(
                    'Bad row length: {}, '
                    'should be at least {} for row {}'.format(
                        len(row), len(HEADER), row))
            row_classes = row[1:]
            if any(class_ not in POSSIBLE_CLASSES for class_ in row_classes):
                raise ValueError(
                    'Unknown class found among: {}'.format(row_classes))
            ids.append(row[0])
            classes.append(row_classes)
    return ids, classes


# POSSIBLE_CLASSES should in the future be modified to be program param.
POSSIBLE_CLASSES = [
    'U-251 MG', 'HeLa', 'PC-3', 'A549', 'MCF7', 'U-2 OS',
    'HEK 293', 'CACO-2', 'RT4']

HEADER = ['filename', 'cell_line']


def score():
    """Run script."""
    parser = argparse.ArgumentParser(
        description=('Scores precision, recall, and f1 score for a '
                     'simple classification challenge.\r\n'
                     'Both solution files and prediction files should '
                     'follow the general format of:\n\n'
                     'filename,cell_line'
                     'ID1,ANSWER1\n'
                     'ID2,ANSWER2\n'
                     '...\n\n'
                     'Note that it is required that all IDs are present '
                     'in both files in the same order.'),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('solution', help='The gold standard solutions')
    parser.add_argument('predictions', help='Predictions from the challenger')
    parser.add_argument('-O', '--output-file', type=str, default=None,
                        help=('Saves output to the specified file in '
                              'csv format.\n'
                              'Default behaviour is to print to stdout '
                              'using spaces as separator characters'))
    args = parser.parse_args()

    binarizer = Binarizer(POSSIBLE_CLASSES)

    solution_ids, solution_classes = parse_solution_file(args.solution)
    bin_solution = binarizer(solution_classes)

    prediction_ids, prediction_classes = parse_solution_file(args.predictions)
    # Make sure that we are working on the same dataset
    if solution_ids != prediction_ids:
        print('The IDs in the two files are unordered or non-equal.')
        print('IDs only in solution:', set(solution_ids) - set(prediction_ids))
        print('IDs only in prediction:', set(
            prediction_ids) - set(solution_ids))
        sys.exit(-1)

    bin_prediction = binarizer(prediction_classes)
    overall_result = precision_recall(bin_prediction, bin_solution, True)

    result = precision_recall(bin_prediction, bin_solution, True, 'class')

    output_file = args.output_file
    if output_file:
        json_result = {
            'data': list(overall_result),
            'additionalData': [
                [result[0][idx], result[1][idx], result[2][idx]]
                for idx, _ in enumerate(binarizer.classes)]}
        with open(args.output_file, 'w') as json_file:
            simplejson.dump(json_result, json_file, ignore_nan=True, indent=2)
        print(simplejson.dumps(json_result, ignore_nan=True, indent=2))
    else:
        print('class', 'pre', 'rec', 'f1')
        for i, class_ in enumerate(binarizer.classes):
            print(class_, result[0][i], result[1][i], result[2][i])
        print('Overall', overall_result[0],
              overall_result[1], overall_result[2])


if __name__ == '__main__':
    score()
