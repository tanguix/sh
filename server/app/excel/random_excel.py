

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# Define the number of rows
num_rows = 1000

# Define date range
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)

# Generate dates
dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
dates = np.random.choice(dates, num_rows)
dates.sort()

# Generate product data
products = ['T-shirt', 'Jeans', 'Dress', 'Jacket', 'Skirt', 'Shoes', 'Handbag']
product_costs = {'T-shirt': 10, 'Jeans': 25, 'Dress': 30, 'Jacket': 40, 'Skirt': 20, 'Shoes': 35, 'Handbag': 45}
products_list = np.random.choice(products, num_rows)

# Generate quantities
quantities = np.random.randint(1, 100, num_rows)

# Calculate costs and revenues
costs = [product_costs[product] * quantity for product, quantity in zip(products_list, quantities)]
revenues = [cost * np.random.uniform(1.2, 1.8) for cost in costs]  # 20-80% markup

# Generate customer types
customer_types = ['Retail', 'Wholesale', 'Online']
customer_types_list = np.random.choice(customer_types, num_rows)

# Generate payment methods
payment_methods = ['Credit Card', 'Cash', 'Bank Transfer', 'PayPal']
payment_methods_list = np.random.choice(payment_methods, num_rows)

# Generate locations
locations = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Miami']
locations_list = np.random.choice(locations, num_rows)

# Create DataFrame
df = pd.DataFrame({
    'Date': dates,
    'Product': products_list,
    'Quantity': quantities,
    'Cost': costs,
    'Revenue': revenues,
    'Profit': np.array(revenues) - np.array(costs),
    'Customer Type': customer_types_list,
    'Payment Method': payment_methods_list,
    'Location': locations_list
})

# Add some additional calculated columns
df['Profit Margin'] = (df['Profit'] / df['Revenue']) * 100
df['Average Sale Price'] = df['Revenue'] / df['Quantity']

# Sort by date
df = df.sort_values('Date')

# Save to Excel
excel_filename = 'fashion_production_financial_data.xlsx'
df.to_excel(excel_filename, index=False)

print(f"Fashion and Production Industry Financial Data file '{excel_filename}' has been created.")
print("File summary:")
print(f"Number of rows: {num_rows}")
print(f"Number of columns: {len(df.columns)}")
print("Column names:")
for col in df.columns:
    print(f"- {col}")

