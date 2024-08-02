

import pandas as pd

class ExcelProcessor:
    @staticmethod
    def get_allowed_operations():
        return ['basic_info', 'statistical_summary', 'full_summary']

    @staticmethod
    def process_excel(filepath, operations):
        df = pd.read_excel(filepath)
        
        results = {}

        if 'basic_info' in operations or 'full_summary' in operations:
            results['basic_info'] = ExcelProcessor._get_basic_info_html(df)

        if 'statistical_summary' in operations or 'full_summary' in operations:
            results['statistical_summary'] = ExcelProcessor._get_statistical_summary_html(df)

        if 'full_summary' in operations:
            results['full_summary'] = f"{results['basic_info']}<br>{results['statistical_summary']}"

        return results

    @staticmethod
    def _get_basic_info_html(df):
        info = f"""
        <h3>Basic Summary:</h3>
        <ul>
            <li>Number of rows: {len(df)}</li>
            <li>Number of columns: {len(df.columns)}</li>
            <li>Column names: {', '.join(df.columns)}</li>
        </ul>
        <h4>Data types:</h4>
        {df.dtypes.to_frame().to_html(classes='table')}
        <h4>First few rows:</h4>
        {df.head().to_html(classes='table')}
        """
        return info

    @staticmethod
    def _get_statistical_summary_html(df):
        summary = df.describe(include='all').to_html(classes='table')
        return f"<h3>Statistical Summary:</h3>{summary}"


