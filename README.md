# Grizly orders

Make order on [grizly.cz](https://grizly.cz).

Script reads a Google spreadsheet with links to products, 
updates prices and puts items to shopping cart.

Spreadsheet needs these specifics:
* order items starts at row 4
* Column F contains links to a product
* Column G contains quantity of product to be ordered
* Columns B-E are filled by script with
  * Name
  * Status
  * Price per package 
  * Weight by package

## Installation

You need poetry ([installation](https://python-poetry.org/docs/#installation)).

Then run `poetry install` to create a virtual environment with installed dependecies.

## Run

Before running you need
* [Google API credentials for Spreadsheets](https://console.cloud.google.com/apis/credentials).
* Prepared Google Spreadsheet (see format above)
* Grizly cookie named `4every1_ses` (after login)

```
poetry run python grizlyorders.py --help
usage: grizlyorders.py [-h] --cookie COOKIE --sheet-id SHEET_ID --worksheet-name WORKSHEET_NAME [--google-api-auth GOOGLE_API_AUTH]

Make order on https://grizly.cz

options:
  -h, --help            show this help message and exit
  --cookie COOKIE       Session cookie named `4every1_ses` after login
  --sheet-id SHEET_ID   Google spreadsheet id that contains shopping list
  --worksheet-name WORKSHEET_NAME
                        Name of a worksheet in spreadsheet
  --google-api-auth GOOGLE_API_AUTH
                        Path to json file with google api auth (default is google_api_auth.json)
```

## Use as a library

```python3
from grizlyorders import Product
my_cookie = "<your-secret-cookie>"
p = Product.from_url("https://www.grizly.cz/grizly-cocka-cerna-beluga-1000-g", session_cookie=my_cookie)
print(p)
# Product(id='13936', name='GRIZLY Čočka černá Beluga 1000 g', price=Decimal('64'), weight=1000, url='https://www.grizly.cz/grizly-cocka-cerna-beluga-1000-g')
p.order(quantity=100, session_cookie=my_cookie)
# now a lot of lentils are in the basket (or OutOfStock is raised)
```

## TODOs

* print nice progress message
* add status column to table
* make orders in async
