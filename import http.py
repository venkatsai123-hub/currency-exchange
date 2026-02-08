import requests
import json
from datetime import date

CACHE_FILE = "rates.json"
API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

# Currency code → Currency name
currency_names = {
    "USD": "US Dollar",
    "INR": "Indian Rupee",
    "EUR": "Euro",
    "JPY": "Japanese Yen",
    "GBP": "British Pound",
    "AUD": "Australian Dollar",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "SGD": "Singapore Dollar",
    "NZD": "New Zealand Dollar",
    "ZAR": "South African Rand",
    "AED": "UAE Dirham",
    "SAR": "Saudi Riyal",
    "KRW": "South Korean Won",
    "THB": "Thai Baht",
    "MYR": "Malaysian Ringgit",
    "IDR": "Indonesian Rupiah",
    "PHP": "Philippine Peso",
    "PKR": "Pakistani Rupee",
    "BDT": "Bangladeshi Taka",
    "LKR": "Sri Lankan Rupee",
    "NPR": "Nepalese Rupee"
}


def fetch_rates_from_api():
    response = requests.get(API_URL, timeout=5)
    data = response.json()
    return data["rates"]


def load_cached_rates():
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except:
        return None


def save_rates_to_cache(rates):
    data = {
        "date": str(date.today()),
        "rates": rates
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def get_rates():
    today = str(date.today())
    cached_data = load_cached_rates()

    if cached_data and cached_data.get("date") == today:
        print("Using cached exchange rates.")
        return cached_data["rates"]

    try:
        print("Fetching latest exchange rates...")
        rates = fetch_rates_from_api()
        save_rates_to_cache(rates)
        return rates
    except:
        if cached_data:
            print("API unavailable. Using cached rates.")
            return cached_data["rates"]
        else:
            print("No data available.")
            return None


def convert_currency(rates, from_cur, to_cur, amount):
    return round(amount * (rates[to_cur] / rates[from_cur]), 2)


def display_top_currencies(rates, top_n=10):
    print("\nTop Strongest Currencies (highest value vs USD):")

    sorted_rates = sorted(rates.items(), key=lambda x: x[1], reverse=True)

    count = 0
    for code, value in sorted_rates:
        name = currency_names.get(code, code)
        print(f"{name} ({code}) : {value}")
        count += 1
        if count == top_n:
            break


def main():
    rates = get_rates()
    if not rates:
        return

    # Show strongest currencies first
    display_top_currencies(rates)

    print("\nAvailable currencies:")
    for code in sorted(rates.keys()):
        name = currency_names.get(code, code)
        print(f"{name} ({code})")

    from_cur = input("\nEnter FROM currency code (e.g., INR): ").upper()
    to_cur = input("Enter TO currency code (e.g., USD): ").upper()

    try:
        amount = float(input("Enter amount: "))
    except ValueError:
        print("Invalid amount.")
        return

    if from_cur not in rates or to_cur not in rates:
        print("Invalid currency.")
        return

    result = convert_currency(rates, from_cur, to_cur, amount)
    print(f"\nConverted Amount: {result} {currency_names.get(to_cur, to_cur)}")


if __name__ == "__main__":
    main()
