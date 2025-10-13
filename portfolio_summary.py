# portfolio_summary.py
import csv

def summarize_portfolio(file_path):
    """
    Reads a portfolio CSV and prints a summary.
    Expected CSV format: Stock, Quantity, Buy_Price, Current_Price
    """
    total_investment = 0
    total_current = 0

    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            print(f"{'Stock':<10} {'Qty':<5} {'Invested':<10} {'Current':<10} {'P/L':<10}")
            print("-" * 50)
            for row in reader:
                stock = row['Stock']
                qty = int(row['Quantity'])
                buy_price = float(row['Buy_Price'])
                current_price = float(row['Current_Price'])

                invested = qty * buy_price
                current = qty * current_price
                pl = current - invested

                total_investment += invested
                total_current += current

                print(f"{stock:<10} {qty:<5} {invested:<10.2f} {current:<10.2f} {pl:<10.2f}")

            print("-" * 50)
            print(f"{'Total':<10} {'':<5} {total_investment:<10.2f} {total_current:<10.2f} {total_current - total_investment:<10.2f}")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except KeyError:
        print("Error: CSV file must have columns: Stock, Quantity, Buy_Price, Current_Price.")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Example usage
if __name__ == "__main__":
    summarize_portfolio("portfolio.csv")
