import sys
import re
import pandas as pd
import pvhelper as pv
import interpareto as ipar



def clean_text_column(df, column_name, words_to_remove, replacement=''):
    """Remove common/stopwords from a DataFrame column using regex word boundaries."""
    df_copy = df.copy()
    if column_name not in df_copy.columns:
        raise ValueError(f"Column '{column_name}' not found in DataFrame")
    
    df_copy[column_name] = df_copy[column_name].astype(str)
    
    for word in words_to_remove:
        pattern = r'\b' + re.escape(word) + r'\b'
        df_copy[column_name] = df_copy[column_name].str.replace(
            pattern, replacement, regex=True, flags=re.IGNORECASE
        )
    
    return df_copy


def extract_common_words(text_series, top_n=25):
    """Extract most common words from text series, excluding Polish banking terms."""
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    from nltk.tokenize import RegexpTokenizer, word_tokenize
    import nltk
    
    stemmer = PorterStemmer()
    
    # Basic text preprocessing
    combined_text = ' '.join(text_series.astype(str))
    combined_text = combined_text.lower()
    combined_text = re.sub('[0-9]+', '', combined_text)  # Remove numbers
    
    # Tokenize and filter
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(combined_text)
    filtered_words = [
        stemmer.stem(w) for w in tokens 
        if len(w) > 2 and w not in stopwords.words('english')
    ]
    
    freq_dist = nltk.FreqDist(filtered_words)
    
    # Filter out Polish banking/business terms
    excluded_patterns = r'polska|grupa|centrum|bank'
    return [
        word for word, count in freq_dist.most_common(top_n)
        if not re.search(excluded_patterns, word)
    ]


def load_polish_tax_data(filepath='2023-pod-2024-08-01.xls'):
    """Load and process Polish CIT taxpayer data from Excel file."""
    # Read Excel with proper headers and skip metadata rows
    df = pd.read_excel(
        filepath,
        header=4,
        skiprows=range(5, 10),
        dtype=str
    ).dropna(how="all")
    
    # Clean column names
    df.columns = df.columns.map(str.strip)
    df.columns = df.columns.map(lambda x: '_'.join(x.split(' ')[:2]).replace(',', ''))
    
    taxpayer_col = 'Nazwa_podatnika'
    
    # Clean taxpayer names by removing common words
    common_words = extract_common_words(df[taxpayer_col])
    df = clean_text_column(df, taxpayer_col, common_words)
    
    # Remove " z " pattern (Polish "with/from") and truncate names
    df[taxpayer_col] = df[taxpayer_col].str.replace(r'\sz\s', ' ', regex=True, flags=re.IGNORECASE)
    df[taxpayer_col] = df[taxpayer_col].str.strip().str[:30]
    
    df.set_index(taxpayer_col, inplace=True)
    
    # Select and convert financial columns to numeric
    financial_keywords = ["przychód", "dochód", 'strata', "podatek", "podstawa", "zysk"]
    numeric_cols = [c for c in df.columns if any(k in c.lower() for k in financial_keywords)]
    
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(" ", ""), errors="coerce")
    
    # Rename to English and return subset
    english_columns = ['Revenue', 'Deductible_costs', 'Profit', 'Loss', 'Tax_base', 'Tax_due']
    df = df[numeric_cols].copy()
    df.columns = english_columns[:len(df.columns)]
    
    return df.head(1000)


def run_taxpayers_example():
    """Generate Pareto visualization for Polish taxpayer data."""
    df = load_polish_tax_data('2023-pod-2024-08-01.xls')
    print(f"Loaded taxpayer data: {df.shape}")
    
    ipar.render(df, 'taxpayers_pareto.html', 
                title='Individual data of CIT taxpayers', warnings=False)
    
    # Optional: generate table view
    try:
        import df2tables as df2t
        df2t.render(df.reset_index(), to_file='taxpayers.html', 
                   title='Individual data of CIT taxpayers')
    except ImportError:
        print("df2tables not available, skipping table generation")


def run_birdstrikes_example():
    """Generate Pareto visualization for bird strike cost data."""
    from vega_datasets import data
    
    df = data.birdstrikes()
    df = df[df['Cost__Repair'] > 0]  # Filter positive costs only
    
    ipar.render(df, 'birdstrikes.html', title='Bird Strike Repair Costs')


def run_movies_example():
    """Generate Pareto visualization for movie financial data."""
    from vega_datasets import data
    
    df = data.movies()
    df.set_index('Title', inplace=True)
    
    # Select columns with financial/rating data
    financial_cols = [col for col in df.columns 
                     if re.search('title|gross|votes|sales', col, re.IGNORECASE)]
    
    movie_data = df[financial_cols]
    ipar.render(movie_data, 'movies.html', title='Movie Financial Performance', 
    warnings=False)
    
    # Optional: generate table view
    try:
        import df2tables as df2t
        df2t.render(movie_data.reset_index(), to_file='movies_table.html',
                   title='Movie Data Table')
    except ImportError:
        print("df2tables not available, skipping table generation")


def main():
    """Run all example visualizations."""
    examples = [
        ("Movies Example", run_movies_example),
        ("Bird Strikes Example", run_birdstrikes_example),
        ("Polish Taxpayers Example", run_taxpayers_example),
    ]
    
    for name, func in examples:
        try:
            print(f"\n--- Running {name} ---")
            func()
            print(f"✓ {name} completed successfully")
        except Exception as e:
            print(f"✗ {name} failed: {e}")
            continue


if __name__ == "__main__":
    main()