import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportion_confint
from sklearn.base import BaseEstimator, TransformerMixin

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

class CustomTransformer(BaseEstimator, TransformerMixin):

    def __init__(self, variables_to_eliminate, categorical_variables, numerical_variables, lower_q=0.005, upper_q=0.995):
        self.variables_to_eliminate = variables_to_eliminate
        self.categorical_variables = [col for col in categorical_variables if col not in variables_to_eliminate]
        self.numerical_variables = [col for col in numerical_variables if col not in variables_to_eliminate]
        self.lower_q = lower_q
        self.upper_q = upper_q

    def fit(self, X, y):
        dict_merged_levesl = {}
        dict_outliers_threshold = {}

        for feature in self.categorical_variables:
            x = X[feature].values
            table = merge_similar_categories(x, y)
            groups = table.index.tolist()
            group_mapping = dict(zip(groups, range(len(groups))))
            dict_merged_levesl[feature] = group_mapping

        for feature in self.numerical_variables:
            x = X[feature].values
            lower_threshold, upper_threshold = np.quantile(x, [self.lower_q, self.upper_q])
            dict_outliers_threshold[feature] = lower_threshold, upper_threshold

        self.dict_merged_levesl = dict_merged_levesl
        self.dict_outliers_threshold = dict_outliers_threshold

        return self

    def transform(self, X, y=None, training=False):
        X_transformed = X.copy()
        X_transformed = X_transformed.drop(columns=self.variables_to_eliminate)

        # grouping categories
        for feature, group_mapping in self.dict_merged_levesl.items():
            for group, value in group_mapping.items():
                X_transformed[feature] = X_transformed[feature].replace(to_replace=group, value=str(value))

        # filtering outliers only if training
        if training:
            final_mask = np.repeat(True, len(X))
            for feature, thresholds in self.dict_outliers_threshold.items():
                lower_threshold, upper_threshold = thresholds
                mask = (lower_threshold <= X_transformed[feature]) & (X_transformed[feature] <= upper_threshold)
                final_mask &= mask
            X_transformed = X_transformed[final_mask]
            self.final_mask = final_mask

        X_transformed = pd.get_dummies(X_transformed, columns=self.categorical_variables, drop_first=True).astype(float)

        return X_transformed