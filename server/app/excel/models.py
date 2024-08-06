

import pandas as pd
import json
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import os
import traceback  # Add this line

class ExcelProcessor:

    EXCEL_FOLDER = 'sheet'



    @staticmethod
    def append_data(filename, data, is_new_file):
        # Ensure filename has .xlsx extension
        if not filename.lower().endswith('.xlsx'):
            filename += '.xlsx'
        
        filepath = os.path.join(ExcelProcessor.EXCEL_FOLDER, filename)
        try:
            new_data = json.loads(data)
            
            # Convert the list of dictionaries to a DataFrame
            new_df = pd.DataFrame(new_data)
            
            # Ensure 'price' and 'unit' columns exist
            if 'price' not in new_df.columns:
                new_df['price'] = ''
            if 'unit' not in new_df.columns:
                new_df['unit'] = 'USD'  # Default to USD if not provided

            if is_new_file:
                if os.path.exists(filepath):
                    return {'error': 'File already exists'}, 400
                new_df.to_excel(filepath, index=False, engine='openpyxl')
            else:
                if not os.path.exists(filepath):
                    return {'error': 'File not found'}, 404
                df = pd.read_excel(filepath, engine='openpyxl')
                
                # Ensure existing DataFrame has 'price' and 'unit' columns
                if 'price' not in df.columns:
                    df['price'] = ''
                if 'unit' not in df.columns:
                    df['unit'] = 'USD'
                
                updated_df = pd.concat([df, new_df], ignore_index=True)
                updated_df.to_excel(filepath, index=False, engine='openpyxl')
            return {'message': 'Data appended successfully'}, 200
        except Exception as e:
            error_traceback = traceback.format_exc()
            error_message = f"Failed to append data: {str(e)}\n\nTraceback:\n{error_traceback}"
            print(error_message)  # This will print to your console/logs
            return {'error': error_message}, 500



    @staticmethod
    def get_allowed_operations():
        return ['basic_info', 'column_distribution', 'aggregation']


    @staticmethod
    def process_excel(filename, operations, selected_columns=None):
        filepath = os.path.join(ExcelProcessor.EXCEL_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return {'error': 'File not found'}, 404

        df = pd.read_excel(filepath)
        
        if df.empty:
            return {'error': 'The Excel file is empty.'}, 400

        if selected_columns:
            df = df[selected_columns]

        results = {}
        if 'basic_info' in operations:
            results['basic_info'] = ExcelProcessor._get_basic_info_html(df)
        if 'column_distribution' in operations:
            results['column_distribution'] = ExcelProcessor._get_column_distribution(df)
        if 'aggregation' in operations:
            results['aggregation'] = ExcelProcessor._get_aggregation(df)
        return results, 200

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
    def _get_column_distribution(df):
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_columns) == 0:
            return "No numeric columns found for distribution analysis."
        plots = []
        for column in numeric_columns:
            fig = go.Figure(data=[go.Histogram(
                x=df[column].dropna(),
                nbinsx=30,
                marker=dict(
                    color='rgba(0, 123, 255, 0.6)',
                    line=dict(color='rgba(0, 0, 0, 1)', width=1)
                )
            )])
            fig.update_layout(
                title={
                    'text': f"Distribution of {column}",
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                xaxis_title=column,
                yaxis_title="Frequency",
                bargap=0.05,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
            plots.append({
                'name': column,
                'plot': json.dumps(fig, cls=PlotlyJSONEncoder)
            })
        return plots



    @staticmethod
    def _get_aggregation(df):
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_columns) == 0:
            return "No numeric columns found for aggregation analysis."
        
        agg_data = df[numeric_columns].agg(['sum', 'mean', 'median', 'min', 'max']).T
        
        # Round the values to 2 decimal places
        agg_data = agg_data.round(2)
        
        # Convert to dictionary for easy JSON serialization
        agg_dict = agg_data.to_dict('index')
        
        return json.dumps(agg_dict)


    @staticmethod
    def get_columns(filename):
        filepath = os.path.join(ExcelProcessor.EXCEL_FOLDER, filename)
        if not os.path.exists(filepath):
            return {'error': 'File not found'}, 404
        df = pd.read_excel(filepath)
        return {'columns': df.columns.tolist()}, 200

    @staticmethod
    def list_excel_files():
        try:
            files = [f for f in os.listdir(ExcelProcessor.EXCEL_FOLDER) if f.endswith(('.xlsx', '.xls'))]
            return files, 200
        except Exception as e:
            return {'error': f'Failed to list Excel files: {str(e)}'}, 500

    @staticmethod
    def save_uploaded_file(file):
        filename = file.filename
        filepath = os.path.join(ExcelProcessor.EXCEL_FOLDER, filename)
        try:
            os.makedirs(ExcelProcessor.EXCEL_FOLDER, exist_ok=True)
            file.save(filepath)
            return {'message': 'File uploaded successfully', 'filepath': filename}, 200
        except OSError as e:
            return {'error': f'Failed to save file due to system error: {str(e)}'}, 500
