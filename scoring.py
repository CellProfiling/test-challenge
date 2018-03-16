#!/usr/bin/python3
import collections
import numpy as np
import argparse
import csv
import sys


def precision_recall(prediction, actual, include_f1=False, mode='total'):
    """
    Calculates the precision and recall for a prediction on a dataset.
    Optionally calculates the f1 score as well.

    Args:
        prediction: A binary matrix representing the predictions on the dataset.
        actual: A binary matrix representing the actual true positives of the dataset.
        include_f1: Whether or not to include f1 in the return values.
        mode: One of 'total' or 'class'.
              In 'total' mode, the entire set is considered.
              In 'class' mode, the precision and recall is calculated for each class individually.
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
        precision = truepos/(truepos + falsepos)
        recall = truepos/(truepos + falseneg)
        if not np.isscalar(precision):
            precision[~np.isfinite(precision)] = 0
            recall[~np.isfinite(recall)] = 0

        if include_f1:
            f1 = 2*(precision*recall)/(precision+recall)

    if include_f1:
        return precision, recall, f1
    return precision, recall


def jaccard_index(y_true, y_predict):
    """
    Calculates the Jaccard index of the predictions on the true values.
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
        The Jaccard index (jaccard similarity) of the predictions on the true labels.
    """
    numerator = 0
    denominator = 0
    for (r, p) in zip(y_true, y_predict):
        if len(r) != len(p):
            raise ValueError('Array lengths do not agree')

        true = set(np.where(r)[0])
        pred = set(np.where(p)[0])

        intersection = true.intersection(pred)
        union = true.union(pred)
        numerator += len(intersection)
        denominator += len(union)
    return numerator/denominator


class Binarizer(object):
    def __init__(self, classes):
        """
        Args:
            classes: A list of the classes that can be binarized.
        """
        self.classes = sorted(set(classes))
        self._index = dict(zip(self.classes, range(len(self.classes))))
        self._reverse_index = dict(zip(range(len(self.classes)), self.classes))

    def bin_label(self, item):
        """
        Binarize a single item.
        If the item is iterable and is not a string, the item will be binarized as a multi-label item.
        """
        bin_ = [0] * len(self.classes)
        if isinstance(item, collections.Iterable) and not isinstance(item, str):
            for c in item:
                bin_[self._index[c]] = 1
        else:
            bin_[self._index[item]] = 1
        return bin_

    def binarize(self, y):
        """
        Args:
            y: A list of of labels to be binarized.
               Items in `y` that are iterable (except strings) will be binarized as a multi-label item,
               all other items will be binarized as a single-label item.
        Returns:
            A list of binarized label lists.
        """
        binarized = []
        for item in y:
            bin_ = self.bin_label(item)
            binarized.append(bin_)
        return binarized

    def unbin_label(self, item):
        unbin = []
        for it in item:
            if it:
                unbin.append(self._reverse_index[it])
        return unbin

    def unbinarize(self, y):
        unbinarized = []
        for item in y:
            unbinarized.append(self.unbin_label(item))
        return unbinarized

    def __iter__(self):
        return self.classes

    def __len__(self):
        return len(self.classes)

    __call__ = binarize


def parse_solution_file(solution_file):
    file_handle = open(solution_file)
    solution_reader = csv.reader(file_handle)
    ids = []
    classes = []

    for row in solution_reader:
        ids.append(row[0])
        classes.append(row[1])
    return ids, classes


# POSSIBLE_CLASSES should in the future be modified to be program param.
POSSIBLE_CLASSES = ['U2OS', 'A431', 'HELA']
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description=('Scores precision, recall, and f1 score for a '
                         'simple classification challenge.\r\n'
                         'Both solution files and prediction files should '
                         'follow the general format of:\n\n'
                         'ID1,ANSWER1\n'
                         'ID2,ANSWER2\n'
                         '...\n\n'
                         'Note that it is required that all IDs are present '
                         'in both files in the same order.'
                         ),
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
    solution = binarizer(solution_classes)

    prediction_ids, prediction_classes = parse_solution_file(args.predictions)
    # Make sure that we are working on the same dataset
    if not solution_ids == prediction_ids:
        print('The IDs in the two files are unordered or non-equal.')
        print('IDs only in solution:', set(solution_ids)-set(prediction_ids))
        print('IDs only in prediction:', set(prediction_ids)-set(solution_ids))
        sys.exit(-1)

    prediction = binarizer(prediction_classes)
    overall_result = precision_recall(prediction, solution, True)

    result = precision_recall(prediction, solution, True, 'class')

    output_file = args.output_file
    if output_file:
        csvfile = open(args.output_file, 'w')
        writer = csv.writer(csvfile)
        writer.writerow(['class', 'pre', 'rec', 'f1'])
        for i, class_ in enumerate(binarizer.classes):
            writer.writerow([class_, result[0][i], result[1][i], result[2][i]])
        writer.writerow(['overall', overall_result[0], overall_result[1], overall_result[2]])
        csvfile.close()
    else:
        print('class', 'pre', 'rec', 'f1')
        for i, class_ in enumerate(binarizer.classes):
            print(class_, result[0][i], result[1][i], result[2][i])
        print('Overall', overall_result[0], overall_result[1], overall_result[2])
