import requests
from django.conf import settings
from .models import GoldPrice, GoldItem
from decimal import Decimal

API_URL = "https://Api.BrsApi.ir/Market/Gold_Currency.php"

def fetch_gold_price():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/131.0.0.0 Safari/537.36 OPR/106.0.0.0",
        "Accept": "application/json, text/plain, */*",
    }
    params = {"key": settings.BRS_API_KEY}

    resp = requests.get(API_URL, headers=headers, params=params, timeout=10)
    if resp.status_code != 200:
        return

    data = resp.json()
    price = data["gold"][0]["price"]
    gp = GoldPrice.objects.create(price_per_gram=price)
    for item in GoldItem.objects.all():
        base = item.weight_gram * gp.price_per_gram
        multiplier = Decimal("1") + (item.profit_percent / Decimal("100"))
        item.final_price = int(base * multiplier)
        item.save()