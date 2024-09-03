import polars as pl

main_schema = {
    'Number': pl.Int64,
    'ISBN': str,
    'Month': str,
    'Year': pl.Int64,
    'Title': str,
    'Score': pl.Float64,
    'Author': str,
    'Publisher': str,
    'Pages': pl.Int64,
    'Author gender': str,
    'Pub year': pl.Int64,
    'Goodreads score': pl.Float64,
    'Our score conversion': pl.Float64,
    'variance': pl.Float64,
    'Debut?': str,
    'Translated?': str,
    'Topics': str
}

resources_schema = {
    'Resource': str,
    'Description': str,
    'URL': str
}