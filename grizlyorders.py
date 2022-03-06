import argparse
from dataclasses import dataclass
from decimal import Decimal

from bs4 import BeautifulSoup

import requests
import re
import gspread

TIMEOUT = 60


class OutOfStock(Exception):
    pass


MAX_ROWS = 200


@dataclass(frozen=True, slots=True)
class Product:
    id: int
    name: str
    price: Decimal
    weight: int
    url: str

    @classmethod
    def from_url(cls, url: str, session_cookie: str) -> 'Product':
        response = requests.get(url, cookies={'4every1_ses': session_cookie}, timeout=TIMEOUT)
        response.raise_for_status()

        document = BeautifulSoup(response.text, "html.parser")

        if len(id_elem := document.select('#product_detail_content form input')) == 0:
            raise OutOfStock('Can not get id')

        weight_match = re.match('(\d+)\s+g', document.select('#product_detail_content a.js-package_item.active > span')[0].text)
        weight = int(weight_match[1]) if weight_match else 0

        return Product(
            id=id_elem[0].attrs['data-pid'],
            name=document.select('#product_detail_content h1')[0].text,
            price=Decimal(re.match(r'\s*(\d+(?:,\d+)?)\s*Kč', document.select('#product_detail_content div.primary')[0].text)[1]),
            weight=weight,
            url=url,
        )

    def order(self, quantity: int, session_cookie: str):
        response = requests.post(
            'https://www.grizly.cz/kosik',
            headers={
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            },
            params={
                'action': 'addpost',
                'ajax': 1,
            },
            data=f'counts[{self.id}]={quantity}',
            cookies={'4every1_ses': session_cookie},
            timeout=TIMEOUT,
        )
        response.raise_for_status()

        response_data = response.json()
        if response_data['isok'] is not True:
            raise OutOfStock('Can not order')

        assert response_data['basketItem']['priceWithVat'] == int(self.price)
        assert response_data['basketItem']['quantity'] == quantity


def order_from_sheet(google_auth:str, sheet_id: str, worksheet_name: str, session_cookie: str) -> dict[Product, int]:
    gc = gspread.service_account(filename=google_auth)

    gsheet = gc.open_by_key(sheet_id)
    wsheet = gsheet.worksheet(worksheet_name)
    links_and_counts = wsheet.get(f'F4:G{MAX_ROWS}')

    # strikethrough all prices
    # TODO remove statuses
    wsheet.format(f"D4:D{MAX_ROWS}", {"textFormat": {"strikethrough": True}})

    ordered_products: dict[Product, int] = {}
    for row, (url, quantity) in enumerate(links_and_counts, start=4):
        if not url or not quantity or (quantity := int(quantity)) <= 0:
            continue

        try:
            print("getting:", url)
            p = Product.from_url(url, session_cookie)
            print("Got:", p)
            p.order(quantity, session_cookie)

            ordered_products[p] = quantity
            wsheet.update(f'B{row}:E{row}', [[p.name, 'ok', str(p.price), p.weight]], value_input_option='user_entered')
            wsheet.format(f"D{row}", {"textFormat": {"strikethrough": False}})

        except OutOfStock as e:
            print(f'Out of stock ({str(e)}): {url}')
            wsheet.update(f'C{row}', f'x ({str(e)})')

    return ordered_products


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Make order on https://grizly.cz')

    parser.add_argument('--cookie', type=str, required=True, help='Session cookie named `4every1_ses` after login')
    parser.add_argument('--sheet-id', type=str, required=True, help='Google spreadsheet id that contains shopping list')
    parser.add_argument('--worksheet-name', type=str, required=True, help='Name of a worksheet in spreadsheet')
    parser.add_argument('--google-api-auth', type=str, required=False, default='google_api_auth.json', help='Path to json file with google api auth (default is google_api_auth.json)')

    args = parser.parse_args()

    ordered_products = order_from_sheet(args.google_api_auth, args.sheet_id, args.worksheet_name , args.cookie)

    print(ordered_products)

