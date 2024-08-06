


import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_excel(filename, num_rows=300):
    # Create a list of column names based on the frontend variables
    columns = [
        'date', 'remarks', 'detailedSubject', 'category', 'quantity',
        'specifications', 'voucherNumber', 'accountSubject', 'debitAmount',
        'creditAmount', 'exchangeRate', 'currency', 'customer', 'paymentStatus', 'status'
    ]

    # Generate sample data for each column
    data = {
        'date': [datetime.now().date() - timedelta(days=x) for x in range(num_rows)],
        'remarks': [f'Transaction {i}' for i in range(1, num_rows + 1)],
        'detailedSubject': np.random.choice(['Sales', 'Purchase', 'Expense', 'Income'], num_rows),
        'category': np.random.choice(['Clothes', 'Buttons', 'Silk', 'Bottles'], num_rows),
        'quantity': np.random.randint(1, 100, num_rows),
        'specifications': [f'Spec {i}' for i in range(1, num_rows + 1)],
        'voucherNumber': [f'V{str(i).zfill(5)}' for i in range(1, num_rows + 1)],
        'accountSubject': np.random.choice(['Cash', 'Bank', 'Accounts Receivable', 'Accounts Payable'], num_rows),
        'debitAmount': np.random.uniform(1000, 10000, num_rows).round(2),
        'creditAmount': np.random.uniform(1000, 10000, num_rows).round(2),
        'exchangeRate': np.random.uniform(1, 2, num_rows).round(4),
        'currency': np.random.choice(['USD', 'EUR', 'CNY'], num_rows),
        'customer': np.random.choice([f'Customer {i}' for i in range(1, 6)], num_rows),  # Only 5 customers
        'paymentStatus': np.random.choice(['Paid', 'Pending', 'Overdue'], num_rows, p=[0.7, 0.2, 0.1]),  # Adjusted probabilities
        'status': np.random.choice(['Active', 'Closed', 'On Hold'], num_rows)
    }

    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)

    # Save to Excel file
    df.to_excel(filename, index=False)
    print(f"Sample Excel file '{filename}' has been generated with {num_rows} rows.")

# Generate the sample Excel file
generate_sample_excel('sample_accounting_data.xlsx', num_rows=300)



