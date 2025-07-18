# InterPareto: Pandas DataFrames to Interactive Pareto Analysis

`interpareto` is a Python utility for creating interactive Pareto charts from `pandas.DataFrame` objects. It generates standalone HTML files with dynamic visualizations using [Plotly.js](https://plotly.com/javascript/)—viewable in any browser without Jupyter notebooks, servers, or frameworks.

## Quick start
```python
import pandas as pd
import interpareto as ipar
sample_df = ipar.generate_pareto_data(100)
ipar.render(sample_df, title="Sample Data Analysis")
```

### Ideal for analyzing:

- Positive numeric values (sales, defects, costs)
- Skewed distributions (few large, many small values)
- Categorical data with measurable impact
- Data w- here the 80/20 principle may apply

### Avoid using with:
- Normally distributed data
- Data with many zero/negative values
- Data without clear categories

## Features
- Converts `pandas.DataFrame` to interactive standalone HTML Pareto charts
- **Dynamic column selection**: Switch between different data columns in real-time
- **80/20 rule visualization**: Automatic calculation and annotation of the 80% threshold
- **Smart data processing**: Automatically detects and removes index-like columns
- **Data cleaning**: Handles NaN values, negatives, and zeros with detailed reporting
- Self-contained HTML files with embedded data—no external dependencies at runtime
- Works independently of web servers—viewable offline in any browser
- **Minimal HTML snippet generation**: Generate embeddable HTML content for Flask or other web frameworks

## Basic usage

```python
import pandas as pd
import interpareto as ipar

# Create sample data
df = pd.DataFrame({
    "Category": ["A", "B", "C", "D", "E"],
    "Revenue": [50000, 30000, 15000, 3000, 2000],
    "Customers": [100, 80, 40, 20, 10]
})

# Generate interactive Pareto chart
ipar.render(
    df,
    title="Revenue Analysis",
    to_file="pareto_chart.html",
    startfile=True
)
```

## Main Functions

### render

```python
ipar.render(
    df: pd.DataFrame,
    to_file: Optional[str] = None,
    title: str = "Pareto dashboard",
    templ_path: str = TEMPLATE_PATH,
    startfile: bool = True,
    warnings: bool = True
) -> Union[str, file_object]
```

**Parameters:**
- `df`: Input pandas DataFrame with numeric columns for analysis
- `to_file`: Output HTML file path. If None, returns HTML string instead of writing file
- `title`: Title for the Pareto dashboard
- `templ_path`: Path to custom HTML template (uses default if not specified)
- `startfile`: If True, automatically opens the generated HTML file in default browser
- `warnings`: If True, displays data processing warnings in the output

**Returns:**
- HTML string if `to_file=None`
- File object if `to_file` is specified

### render_inline

```python
ipar.render_inline(
    df: pd.DataFrame,
    **kwargs
) -> str
```

Generates minimal HTML content suitable for embedding in Flask or other web framework templates. This function:
- Returns only the chart markup and JavaScript
- Excludes full HTML document structure (no `<html>`, `<head>`, `<body>` tags)
- **Important**: Requires Plotly.js to be loaded in the host page
- Perfect for embedding interactive Pareto analysis in existing web applications

**Parameters:**
- Same as `render()` except `to_file` is not allowed (always returns string)

### generate_pareto_data

```python
ipar.generate_pareto_data(N: int = 15) -> pd.DataFrame
```

Generates sample data following various statistical distributions for testing and demonstration purposes.

**Parameters:**
- `N`: Number of data points to generate

**Returns:**
- DataFrame with sample data including Pareto, normal, uniform, and other distributions

## Data Processing Features

### Automatic Data Cleaning

InterPareto automatically processes your data to ensure optimal visualization:

- **Index-like column detection**: Removes columns that appear to be indices or sequential numbers
- **Duplicate index handling**: Removes duplicate row indices, keeping the first occurrence
- **Numeric column selection**: Automatically selects the first 10 numeric columns
- **Missing value handling**: Removes rows with NaN values
- **Negative and zero filtering**: Excludes rows with negative values or zeros (configurable)

### Processing Warnings

The library provides detailed feedback about data processing:

```python
# Example processing output
"""
Dropped column 'ID': looks like index
Column 'Revenue': 2 NaNs, (1 negative values, 3 zeros)
Column 'Customers': 0 NaNs, (0 negative values, 1 zeros)
"""
```

## Web Framework Integration

### Complete Flask Example

Here's a complete Flask application demonstrating how to embed interactive Pareto charts:

```python
from flask import Flask, render_template_string
import interpareto as ipar

app = Flask(__name__)

@app.route("/")
def home():
    # Generate sample data (or use your own DataFrame)
    df = ipar.generate_pareto_data(50)
    
    df_title = "Pareto Chart Rendered inline in <strong>Flask</strong>"
    
    # Generate the embeddable Pareto chart HTML
    string_pareto = ipar.render_inline(df, title=df_title, warnings=False)
    
    return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Flask Pareto Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            
            <!-- Required: Plotly.js for chart rendering -->
            <script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.26.0/plotly.min.js"></script>
            
            <style>
                body {
                    font-family: "Segoe UI", Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    text-align: center;
                    margin-bottom: 30px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>My Flask Pareto Dashboard</h1>
                {{ inline_pareto | safe }}
            </div>
        </body>
        </html>
        """,
        inline_pareto=string_pareto,
    )

if __name__ == "__main__":
    app.run(debug=True)
```

**Key points for web framework integration:**

- **Required dependency**: Always include Plotly.js in your host page
- **Self-contained data**: The `render_inline()` function includes all chart data and initialization code
- **Interactive features**: Full column switching and hover functionality preserved
- **Responsive design**: Charts automatically adapt to container size

## Understanding Pareto Analysis

### The 80/20 Rule

Pareto analysis is based on the Pareto Principle (80/20 rule), which states that roughly 80% of effects come from 20% of causes. InterPareto automatically:

- **Sorts data**: Orders values from highest to lowest
- **Calculates cumulative percentages**: Shows running totals as percentage of whole
- **Identifies the 80% threshold**: Highlights where 80% of total value is reached
- **Annotates key insights**: Shows what percentage of categories contribute to 80% of value

### Chart Components

The generated Pareto chart includes:

1. **Horizontal bar chart**: Shows individual values for each category
2. **Cumulative line**: Displays running percentage total
3. **80% threshold line**: Horizontal dashed line at 80%
4. **Intersection annotation**: Shows where cumulative line crosses 80%
5. **Dynamic controls**: Dropdown to switch between different data columns

## Customization Examples

### Basic Usage

```python
import pandas as pd
import interpareto as ipar

# Simple example
df = pd.DataFrame({
    "Product": ["A", "B", "C", "D"],
    "Sales": [100, 80, 60, 40],
    "Profit": [30, 25, 15, 10]
})

# Generate chart
ipar.render(df, title="Sales Analysis", to_file="sales_pareto.html")
```

### Advanced Usage

```python
# Disable warnings for clean output
html_content = ipar.render(
    df,
    title="Custom Pareto Analysis",
    warnings=False,
    to_file=None  # Return HTML string
)

# Use custom template
ipar.render(
    df,
    title="Branded Analysis",
    templ_path="custom_pareto_template.html",
    to_file="branded_pareto.html"
)

# Generate sample data for testing
sample_df = ipar.generate_pareto_data(100)
ipar.render(sample_df, title="Sample Data Analysis")
```

## Requirements

- Python 3.7+
- pandas
- numpy

## Technical Details

### Data Processing Pipeline

1. **Column Detection**: Identifies and removes index-like columns
2. **Duplicate Handling**: Removes duplicate indices
3. **Numeric Selection**: Selects first 10 numeric columns
4. **Data Cleaning**: Removes NaN, negative, and zero values
5. **Pareto Calculation**: Sorts data and calculates cumulative percentages

### Chart Features

- **Interactive tooltips**: Hover for detailed information
- **Column switching**: Real-time data column selection
- **Responsive design**: Adapts to different screen sizes
- **Export options**: Built-in Plotly export functionality
- **Zoom and pan**: Interactive chart exploration

### Template System

Templates use [comnt](https://github.com/ts-kontakt/comnt), a minimal markup system:

```html
<!--[title-->
Dashboard Title
<!--title]-->

const data = /*[p_data*/ [...] /*p_data]*/;
```
## Error Handling

The module includes  error handling for:
- **Data validation**: Ensures numeric columns are available
- **Missing values**: Graceful handling of NaN and missing data
- **Column compatibility**: Validates data types and formats
- **Template loading**: Fallback options for missing templates




MIT License  
© Tomasz Sługocki

