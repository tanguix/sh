

import pandas as pd
import json
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import os
import traceback  # Add this line
from app.logger import logger



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
    def process_excel(filename, operations, selected_columns=None, group_by_column=None, group_by_values=None, aggregate_column=None):
        filepath = os.path.join(ExcelProcessor.EXCEL_FOLDER, filename)
        
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return {'error': 'File not found'}, 404

        df = pd.read_excel(filepath)
        
        if df.empty:
            logger.error("The Excel file is empty.")
            return {'error': 'The Excel file is empty.'}, 400

        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        logger.info(f"DataFrame dtypes: {df.dtypes}")

        results = {}

        if 'basic_info' in operations:
            results['basic_info'] = ExcelProcessor._get_basic_info(df)

        if 'column_distribution' in operations:
            if selected_columns:
                df_selected = df[selected_columns]
                results['column_distribution'] = ExcelProcessor._get_column_distribution(df_selected)
            else:
                logger.warning("No columns selected for distribution analysis.")


        if 'aggregation' in operations:
            if group_by_column and aggregate_column:
                if group_by_column not in df.columns:
                    logger.error(f"Group by column '{group_by_column}' not in dataframe")
                    results['aggregation'] = json.dumps({"error": f"Group by column '{group_by_column}' not in dataframe"})
                elif aggregate_column not in df.columns:
                    logger.error(f"Aggregate column '{aggregate_column}' not in dataframe")
                    results['aggregation'] = json.dumps({"error": f"Aggregate column '{aggregate_column}' not in dataframe"})
                else:
                    logger.info(f"Performing grouped aggregation. Group by: {group_by_column}, Aggregate: {aggregate_column}")
                    results['aggregation'] = ExcelProcessor._get_grouped_aggregation(df, group_by_column, group_by_values, aggregate_column)
            else:
                logger.warning("Missing group by column or aggregate column for aggregation analysis.")

        logger.info(f"Results keys: {results.keys()}")
        return results, 200





    @staticmethod
    def _get_basic_info(df):
        if 'creditAmount' not in df.columns or 'category' not in df.columns:
            return json.dumps({"error": "Required columns 'creditAmount' or 'category' not found in the dataframe"})

        # Group by category and sum creditAmount
        category_sums = df.groupby('category')['creditAmount'].sum().sort_values(ascending=False)

        # Create a pie chart
        fig = go.Figure(data=[go.Pie(
            labels=category_sums.index,
            values=category_sums.values,
            textinfo='label+percent',
            insidetextorientation='radial'
        )])
        
        fig.update_layout(
            title={
                'text': 'Distribution of Credit Amount by Category',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 16}
            },
            margin=dict(l=20, r=20, t=80, b=20),  # Increased top margin
            autosize=True,
        )

        # Extend pie colors to avoid repetition
        fig.update_layout(
            extendpiecolors=True
        )

        fig_json = json.dumps(fig, cls=PlotlyJSONEncoder)
        return {"plot": fig_json}





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
    def _get_grouped_aggregation(df, group_by_column, group_by_values, aggregate_column):
        if not pd.api.types.is_numeric_dtype(df[aggregate_column]):
            logger.error(f"Aggregate column {aggregate_column} is not numeric. dtype: {df[aggregate_column].dtype}")
            return json.dumps({"error": f"Aggregate column '{aggregate_column}' must be numeric"})

        # If group_by_values are provided, filter the dataframe
        if group_by_values:
            group_by_values = [value.strip() for value in group_by_values.split(',')]
            df = df[df[group_by_column].isin(group_by_values)]
            logger.info(f"Filtered dataframe for group_by_values: {group_by_values}")

        grouped = df.groupby(group_by_column)[aggregate_column].agg(['sum', 'mean', 'median', 'min', 'max'])
        grouped = grouped.round(2)  # Round to 2 decimal places

        # Convert to dictionary for easy JSON serialization
        grouped_dict = grouped.to_dict('index')

        logger.info(f"Grouped aggregation result: {json.dumps(grouped_dict)}")
        return json.dumps(grouped_dict)

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

    @staticmethod
    def get_allowed_operations():
        return ['basic_info', 'column_distribution', 'aggregation']


