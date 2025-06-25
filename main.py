
import pandas as pd
import requests
from pprint import pprint


def get_category():
    url = 'https://catalog.wb.ru/brands/v2/catalog?ab_testing=false&appType=1&brand=27445&curr=rub&dest=-1255987&hide_dtype=13&lang=ru&page=1&sort=popular&spp=30'

    response = requests.get(url)
    pprint(response.json())
    return response.json()


def prepare_item(response: dict) -> list[dict]:
    if not response:
        return []

    products_raw = response.get("data", {}).get("products") or []
    result: list[dict] = []

    for product in products_raw:
        # ищем первую size, где присутствует словарь price
        price_dict = {}
        for size in product.get("sizes", []):
            price_dict = size.get("price") or {}
            if price_dict:
                break          # нашли – выходим из цикла

        result.append(
            {
                "name":            product.get("name"),
                "price_basic":     float(price_dict.get("basic")) / 100 if price_dict.get("basic") else None,
                "price_product":   price_dict.get("product") / 100 if price_dict.get("product") else None,
                "rating":          product.get("rating"),
                "reviewRating":    product.get("reviewRating"),
            }
        )
    return result


def main():
    response = get_category()
    prepare_item(response)
    df = pd.DataFrame(prepare_item(response))
    df.to_csv('wb.csv', index=False, encoding='utf-8')
    pprint(
        df.head(10)
    )



if __name__ == '__main__':
    main()

