



import pandas as pd
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_chinese(string):
    return bool(re.search('[\u4e00-\u9fff]', string))

def extract_and_analyze(input_file):
    try:
        xls = pd.ExcelFile(input_file)
        logging.info(f"File '{input_file}' read successfully. Available sheets: {xls.sheet_names}")
        
        all_unique_columns = set()
        mingxi_value_counts = {}
        mingxi_to_kuaiji = {}
        total_rows = 0
        
        for sheet_name in xls.sheet_names:
            logging.info(f"Processing sheet: {sheet_name.strip()}")
            
            df = pd.read_excel(input_file, sheet_name=sheet_name.strip(), header=None)
            
            for index, row in df.iterrows():
                if any(isinstance(cell, str) and '明细科目' in cell for cell in row):
                    header_row = index
                    break
            else:
                logging.warning(f"Could not find a row with '明细科目' in sheet '{sheet_name}'")
                continue
            
            df.columns = df.iloc[header_row]
            df = df.drop(df.index[:header_row+1]).reset_index(drop=True)
            
            df.columns = df.columns.astype(str)
            all_unique_columns.update(df.columns)
            total_rows += len(df)
            
            if '明细科目' in df.columns and '会计科目' in df.columns:
                for mingxi, kuaiji in zip(df['明细科目'].astype(str), df['会计科目'].astype(str)):
                    if mingxi not in mingxi_value_counts:
                        mingxi_value_counts[mingxi] = 0
                    mingxi_value_counts[mingxi] += 1
                    
                    if is_chinese(mingxi) and mingxi not in mingxi_to_kuaiji:
                        mingxi_to_kuaiji[mingxi] = kuaiji
            else:
                logging.warning(f"Column '明细科目' or '会计科目' not found in sheet '{sheet_name}'")
        
        logging.info("Extraction and analysis complete.")
        return all_unique_columns, mingxi_value_counts, mingxi_to_kuaiji, total_rows
    
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return set(), {}, {}, 0

def count_unique_values(input_file, columns):
    try:
        xls = pd.ExcelFile(input_file)
        unique_value_counts = {col: {} for col in columns}
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(input_file, sheet_name=sheet_name.strip(), header=None)
            
            for index, row in df.iterrows():
                if any(isinstance(cell, str) and '明细科目' in cell for cell in row):
                    header_row = index
                    break
            else:
                continue
            
            df.columns = df.iloc[header_row]
            df = df.drop(df.index[:header_row+1]).reset_index(drop=True)
            df.columns = df.columns.astype(str)
            
            for col in columns:
                if col in df.columns:
                    value_counts = df[col].astype(str).value_counts()
                    for value, count in value_counts.items():
                        if value not in unique_value_counts[col]:
                            unique_value_counts[col][value] = 0
                        unique_value_counts[col][value] += count
        
        return unique_value_counts
    
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return {}

def main():
    input_file = input("Please enter the path to your Excel file: ")
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Analyze '明细科目' and '会计科目'")
        print("2. Count unique values in specific columns")
        print("3. Exit")
        
        choice = input("Enter your choice (1, 2, or 3): ")
        
        if choice == '1':
            unique_columns, mingxi_value_counts, mingxi_to_kuaiji, total_rows = extract_and_analyze(input_file)
            
            print(f"\nTotal number of rows in the DataFrame: {total_rows}")
            print("\nUnique column names:")
            for col in sorted(unique_columns):
                print(f"- {col}")
            print("\nUnique values in '明细科目' with their counts and corresponding '会计科目' (if Chinese):")
            for value, count in mingxi_value_counts.items():
                output = f"- {value}: {count}"
                if is_chinese(value) and value in mingxi_to_kuaiji:
                    output += f" (会计科目: {mingxi_to_kuaiji[value]})"
                print(output)
        
        elif choice == '2':
            columns = input("Enter the column names you want to analyze (comma-separated): ").split(',')
            columns = [col.strip() for col in columns]
            unique_value_counts = count_unique_values(input_file, columns)
            
            for col, value_counts in unique_value_counts.items():
                print(f"\nUnique values in '{col}':")
                for value, count in sorted(value_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"- {value}: {count}")
        
        elif choice == '3':
            print("Exiting the program. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()



