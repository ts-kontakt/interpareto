import json
import os
import subprocess
import sys
from functools import partial

TEMPLATE_FILE = "par_template.html"
try:
    # python 3.9+
    from importlib import resources

    TEMPLATE_PATH = str(resources.files("interpareto").joinpath(TEMPLATE_FILE))
except ImportError:
    TEMPLATE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), TEMPLATE_FILE
    )

try:
    from .comnt import get_tag_content
    from .comnt import render as c_render
except ImportError:
    from comnt import get_tag_content
    from comnt import render as c_render

import numpy as np
import pandas as pd


def is_index_like(series, tolerance=0.1):
    # Check if series is empty
    if len(series) == 0:
        return False

    # Check if series has only one element
    if len(series) == 1:
        return True

    # Check if all values are numeric
    if not pd.api.types.is_numeric_dtype(series):
        return False

    # Check for NaN values
    if series.isnull().any():
        return False

    # Calculate differences between consecutive elements
    consecutive_diffs = series.diff().dropna()

    # Check if all differences are approximately equal (consistent step)
    if len(consecutive_diffs) > 0:
        first_step = consecutive_diffs.iloc[0]

        # For integer-like steps, use exact comparison
        if abs(first_step - round(first_step)) < tolerance:
            rounded_step = round(first_step)
            step_consistency = all(abs(diff - rounded_step) < tolerance for diff in consecutive_diffs)
        else:
            # For floating point steps, use tolerance-based comparison
            step_consistency = all(abs(diff - first_step) < tolerance for diff in consecutive_diffs)

        return step_consistency

    return False


def process_df(df: pd.DataFrame):
    processed_df = df.copy()

    # Check if index is already string type
    if not (processed_df.index.dtype == "object" or pd.api.types.is_string_dtype(processed_df.index)):
        # does not help for plotly treats numeric strings as numbers
        processed_df.set_index(processed_df.index.map(lambda x: str(x)), inplace=True)

    # processed_df.index = pd.Index([str(i) for i in processed_df.index])
    processing_messages = []
    for column_name in processed_df.columns:
        column_values = processed_df[column_name]
        print(column_name, is_index_like(column_values))
        if is_index_like(column_values):
            processing_messages.append(f"Dropped column '<b>{column_name}</b>': looks like index")
            processed_df.drop(columns=[column_name], axis=1, inplace=True)

    if not processed_df.index.is_unique:
        duplicate_counts = repr(processed_df.index.value_counts().nlargest(3))
        processing_messages.append(f"Dropped duplicate index: {duplicate_counts}")

        processed_df = processed_df[~processed_df.index.duplicated(keep="first")]
    
    # Select numeric columns and slice first 10
    numeric_columns = processed_df.select_dtypes(include="number")
    # print(numeric_columns)
    first_ten_numeric = numeric_columns.iloc[:, :10]

    for column_name in first_ten_numeric.columns:
        column_values = first_ten_numeric[column_name]
        print(column_name, is_index_like(column_values))
        if is_index_like(column_values):
            print("!drop", column_name)
            processing_messages.append(f"Column '{column_name}': looks like index")
            first_ten_numeric.drop(columns=[column_name], axis=1, inplace=True)

        nan_count = column_values.isna().sum()
        negative_count = (column_values < 0).sum()
        zero_count = (column_values == 0).sum()

        if nan_count > 0 or negative_count > 0 or zero_count > 0:
            processing_messages.append(
                f"Column '<b>{column_name}</b>': {nan_count} NaNs, ({negative_count} negative values, {zero_count} zeros)"
            )
    
    first_ten_numeric.dropna(inplace=True)
    first_ten_numeric = first_ten_numeric[~(first_ten_numeric == 0).any(axis=1)]
    
    messages_summary = (
        "</br>".join(processing_messages)
        if processing_messages
        else "No NaNs, negatives, or zeros found."
    )
    return first_ten_numeric, messages_summary


def generate_smoothed_pareto_column(N, base_high=5000, noise=1):
    position_ranks = np.arange(1, N + 1)
    pareto_values = base_high / position_ranks  # decay with rank
    pareto_values += np.random.uniform(-noise, noise, size=N) * pareto_values  # smooth randomness
    # pareto_values = replace_outliers_with_mean(pareto_values)
    np.random.shuffle(pareto_values)
    return pareto_values


def generate_pareto_data(N=15):
    np.random.seed(42)

    sample_data = {
        "Range to drop": range(N),
        "smoothed_pareto_A": generate_smoothed_pareto_column(N, base_high=200),
        "smoothed_pareto_B": generate_smoothed_pareto_column(N, base_high=10000),
        "smoothed_pareto_C": generate_smoothed_pareto_column(N, base_high=6000),
        "normal_mean_30_std_5": np.random.normal(
            loc=30, scale=1, size=N
        ),  # .clip(min=0),
        "uniform_0_to_1000": np.random.uniform(-5, 10, size=N),
        "poisson_lambda_15": np.random.poisson(lam=15, size=N),
        "beta_scaled_0_to_100": (np.random.beta(a=2, b=5, size=N) * 100),
        "binomial_n100_p0.2": np.random.binomial(n=100, p=0.2, size=N),
        "zipf_a1.5_clipped": np.clip(np.random.zipf(a=1.5, size=N), 1, 500),
        "gamma_shape_2_scale_20": np.random.gamma(shape=2.0, scale=20.0, size=N),
    }

    result_df = pd.DataFrame(sample_data).round(2)
    return result_df


def open_file(filename):
    if sys.platform.startswith("win"):
        os.startfile(filename)
    else:
        file_opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([file_opener, filename])


def render(
    df,
    to_file=None,
    title="Pareto dashboard",
    templ_path=TEMPLATE_PATH,
    startfile=True,
    warnings=True,
):
    processed_df, processing_info = process_df(df)
    column_headers = ["index"] + processed_df.columns.tolist()
    tabular_data = [[row_index] + row_values.tolist() for row_index, row_values in processed_df.iterrows()]

    data_json_string = json.dumps(tabular_data, separators=(",", ":"))
    headers_json_string = json.dumps(column_headers, separators=(",", ":"))

    warning_info = f"<p class='warn'>{processing_info}</p>" if warnings else ""

    template_variables = {
        "p_data": data_json_string,
        "col_names": headers_json_string,
        "title": title,
        "warn": warning_info,
        # "long_col": headers_json_string,
        # "titles": headers_json_string,
    }
    with open(templ_path, encoding="utf-8") as template_file:
        template_content = template_file.read()
    
    rendered_html = c_render(template_content, template_variables)
    
    if not to_file:
        return rendered_html
    
    assert templ_path != to_file and templ_path not in to_file
    with open(to_file, "w", encoding="utf8") as output_file:
        output_file.write(rendered_html)
    
    if startfile:
        open_file(to_file)
    
    return output_file


_render_str = partial(render, to_file=None)


def render_inline(df, **kwargs):
    if "to_file" in kwargs:
        print(
            f"wrong argument:[to_file] {kwargs.pop('to_file')} is not allowed in render_inline"
        )
        # del kwargs['to_file']
    
    inline_html = _render_str(df, **kwargs)
    minimal_content = c_render(
        get_tag_content("min_content", inline_html), {"render_inline": "true"}
    )
    return minimal_content


def main():
    output_filename = "demo.html"
    demo_df = generate_pareto_data(100)
    render(demo_df, to_file=output_filename)


if __name__ == "__main__":
    main()