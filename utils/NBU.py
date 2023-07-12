import requests
import json


def get_exchange_rate():
    url = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=USD&json'

    response = requests.get(url)
    data = json.loads(response.text)

    if len(data) > 0:
        exchange_rate = data[0]['rate']
        return exchange_rate
    else:
        return 0
