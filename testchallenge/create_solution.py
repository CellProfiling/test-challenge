"""Create final solution csv file."""
import pandas as pd


def create_solution(solution, renaming):
    """Create final solution csv file."""
    solution = pd.read_csv(solution, header=0, dtype=str)
    names = pd.read_csv(renaming, header=0, dtype=str)
