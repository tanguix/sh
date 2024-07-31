

import pandas as pd

class ExcelProcessor:
    @staticmethod
    def get_allowed_operations():
        return ['sum', 'average', 'max', 'min']

    @staticmethod
    def process_excel(filepath):
        df = pd.read_excel(filepath)
        summary = f"""
        Excel File Summary:
        - Number of rows: {len(df)}
        - Number of columns: {len(df.columns)}
        - Column names: {', '.join(df.columns)}
        - Data types:
        {df.dtypes.to_string()}
        
        - First few rows:
        {df.head().to_string()}
        """
        return summary




