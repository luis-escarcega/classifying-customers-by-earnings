import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportion_confint

def cross_tab(x, y):
    table = pd.crosstab(x, y)
    table.columns = ["negative", "positive"]
    index = table.index.tolist()
    index = [(idx,) for idx in index]
    table.index = index
    return table

def confidence_interval(negative_count, positive_count):
    lower_ci, higher_ci = proportion_confint(
        count=positive_count,
        nobs=positive_count+negative_count,
        alpha=0.01,
        method='agresti_coull')
    return lower_ci, higher_ci

def _there_is_intersection(ci_i, ci_j):
    x_i, y_i = ci_i
    x_j, y_j = ci_j
    return np.minimum(y_i, y_j) - np.maximum(x_i, x_j) > 0

def there_is_intersection(table, i, j):
    """Constructs the confidence intervarls for categories i and j"""
    negative_count_i, positive_count_i = table.iloc[i]
    negative_count_j, positive_count_j = table.iloc[j]

    ci_i = confidence_interval(negative_count_i, positive_count_i)
    ci_j = confidence_interval(negative_count_j, positive_count_j)

    return _there_is_intersection(ci_i, ci_j)

def merge_categories(table, i, j):
    """Removes category j and add it to i"""
    index = table.index.tolist()
    category_i = index[i]
    category_j = index[j]

    table.iloc[i] = table.iloc[i] + table.iloc[j]
    table = table.drop(category_j, axis=0)
    index[i] = index[i] + index[j]
    index.pop(j)

    table.index = index
    return table

def merge_similar_categories(x, y):
    table = cross_tab(x, y)
    n = len(table)
    i = 0
    while i < n:
        j = i + 1
        while j < n:
            if there_is_intersection(table, i, j):
                table = merge_categories(table, i, j)
                n -= 1
            else:
                j += 1
        i += 1
    table["proportion"] = table["positive"] / (table["positive"] + table["negative"])
    table = table.sort_values("proportion")
    return table