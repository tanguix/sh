
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# Define the number of rows and columns
num_rows = 100
num_numeric_columns = 5
num_categorical_columns = 3
num_date_columns = 2

# Generate numeric data
numeric_data = {f'Numeric_{i+1}': np.random.randint(1, 1000, num_rows) for i in range(num_numeric_columns)}

# Generate categorical data
categories = ['Category A', 'Category B', 'Category C', 'Category D', 'Category E']
categorical_data = {f'Categorical_{i+1}': [random.choice(categories) for _ in range(num_rows)] for i in range(num_categorical_columns)}

# Generate date data
start_date = datetime(2020, 1, 1)
date_data = {f'Date_{i+1}': [start_date + timedelta(days=np.random.randint(0, 1095)) for _ in range(num_rows)] for i in range(num_date_columns)}

# Combine all data
data = {**numeric_data, **categorical_data, **date_data}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
excel_filename = '../../sheet/random_data.xlsx'
df.to_excel(excel_filename, index=False)

print(f"Random Excel file '{excel_filename}' has been created.")
print("File summary:")
print(f"Number of rows: {num_rows}")
print(f"Number of columns: {len(df.columns)}")
print("Column names:")
for col in df.columns:
    print(f"- {col}")
