import requests
import json
from datetime import date

API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
CACHE_FILE = "rates.json"


def fetch_rates_from_api():
    """Fetch latest rates from API"""
    response = requests.get(API_URL, timeout=5)
    data = response.json()
    return data["rates"]


def load_cached_rates():
    """Load rates from cache file if available"""
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
            return data["rates"]
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_rates_to_cache(rates):
    """Save rates to cache file with today's date"""
    data = {
        "date": str(date.today()),
        "rates": rates
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def get_rates():
    """Get rates from API, fallback to cache if needed"""
    try:
        print("Fetching latest rates from API...")
        rates = fetch_rates_from_api()

        # Save fresh data to cache
        save_rates_to_cache(rates)
        return rates

    except Exception:
        print("Internet not available. Loading cached rates...")
        cached_rates = load_cached_rates()

        if cached_rates:
            return cached_rates
        else:
            print("No cached data available.")
            return None


def convert_currency(rates, from_cur, to_cur, amount):
    """Convert between currencies using ratio formula"""
    return round(amount * (rates[to_cur] / rates[from_cur]), 2)


def main():
    rates = get_rates()

    if not rates:
        return

    print("\nAvailable currencies:")
    print(", ".join(sorted(rates.keys())))

    from_cur = input("\nEnter FROM currency: ").upper()
    to_cur = input("Enter TO currency: ").upper()

    try:
        amount = float(input("Enter amount: "))
    except ValueError:
        print("Invalid amount.")
        return

    if from_cur not in rates or to_cur not in rates:
        print("Invalid currency code.")
        return

    result = convert_currency(rates, from_cur, to_cur, amount)
    print(f"\nConverted Amount: {result} {to_cur}")


if __name__ == "__main__":
    main()
