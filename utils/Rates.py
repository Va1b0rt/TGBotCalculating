import requests

from bs4 import BeautifulSoup


url = 'https://minfin.com.ua/currency/{0}/{1}/'


def get_rate_in_date(currency: str, date: str) -> float:
    """
    currency - eur, usd
    date - str date in format 2023-12-17

    return: str currency rate
    """
    _url = url.format(currency, date)

    rate_page = requests.get(_url).text
    catalog_soup = BeautifulSoup(rate_page, 'html.parser')
    items = catalog_soup.find_all(class_="sc-1x32wa2-9 bKmKjX")
    items = [item for item in items if item.get('type') is None]

    return float(items[0].text.split('.')[0].replace(',', '.').replace('-', ''))


if __name__ == "__main__":
    rate = get_rate_in_date('eur', '2023-09-07')
    assert isinstance(rate, float), 'rate не является float'
    print(rate)

