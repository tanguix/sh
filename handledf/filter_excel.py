



import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def filter_and_calculate(input_file, output_file, filter_conditions):
    try:
        xls = pd.ExcelFile(input_file)
        logging.info(f"File '{input_file}' read successfully. Available sheets: {xls.sheet_names}")
        
        for sheet_name in xls.sheet_names:
            logging.info(f"Processing sheet: {sheet_name.strip()}")
            
            df = pd.read_excel(input_file, sheet_name=sheet_name.strip(), header=None)
            
            for index, row in df.iterrows():
                if any(isinstance(cell, str) and '明细科目' in cell for cell in row):
                    header_row = index
                    break
            else:
                logging.warning(f"Could not find a row with Chinese characters in sheet '{sheet_name}'")
                continue

            df.columns = df.iloc[header_row]
            df = df.drop(df.index[:header_row+1]).reset_index(drop=True)
            
            # Convert all column names to strings
            df.columns = df.columns.astype(str)
            
            logging.info(f"Columns in this sheet: {', '.join(df.columns)}")
            
            filtered_df = df.copy()
            for column, value in filter_conditions.items():
                if column in df.columns:
                    filtered_df = filtered_df[filtered_df[column] == value]
                else:
                    logging.warning(f"Column '{column}' not found in sheet '{sheet_name}'")
            
            if not filtered_df.empty:
                # Convert '贷方金额' and '借方金额' to numeric, replacing non-numeric values with 0
                filtered_df['贷方金额'] = pd.to_numeric(filtered_df['贷方金额'], errors='coerce').fillna(0)
                filtered_df['借方金额'] = pd.to_numeric(filtered_df['借方金额'], errors='coerce').fillna(0)
                
                # Calculate the difference
                total_credit = filtered_df['贷方金额'].sum()
                total_debit = filtered_df['借方金额'].sum()
                difference =  total_debit - total_credit
                
                logging.info(f"Total Credit (贷方金额): {total_credit}")
                logging.info(f"Total Debit (借方金额): {total_debit}")
                logging.info(f"Difference (Credit - Debit): {difference}")
                
                # Add the calculation results to the DataFrame
                new_row = pd.DataFrame({
                    '摘要': ['Total'],
                    '贷方金额': [total_credit],
                    '借方金额': [total_debit],
                    '明细科目': [f'利润: {difference}']
                })
                filtered_df = pd.concat([filtered_df, new_row], ignore_index=True)
                
                filtered_df.to_excel(output_file, index=False)
                logging.info(f"Filtered data with calculation saved to {output_file}")
                logging.info(f"Number of rows in the filtered file: {len(filtered_df)}")
                return
            else:
                logging.warning(f"No data matching the filter conditions in sheet '{sheet_name}'")
        
        logging.warning("No data matching the filter conditions found in any sheet of the Excel file.")
    
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)

# Example usage
input_file = './test.xlsx'
output_file = 'filtered_output_with_calculation.xlsx'
filter_conditions = {
    '明细科目': 'HB44181',
    # Add more conditions here if needed, e.g., '会计科目': '原材料'
}

filter_and_calculate(input_file, output_file, filter_conditions)






