


import requests

class ExchangeRate:
    ENDPOINT = 'https://api.exchangeratesapi.io/v1/latest'
    ACCESS_KEY = '41f3aa2c148201fc12542c1ce270f6a6'
    BASE_CURRENCY = 'EUR'
    SYMBOLS = ['CNY', 'JPY', 'USD', 'CAD']

    @staticmethod
    def get_latest_rate():
        url = f'{ExchangeRate.ENDPOINT}?access_key={ExchangeRate.ACCESS_KEY}&base={ExchangeRate.BASE_CURRENCY}&symbols={",".join(ExchangeRate.SYMBOLS)}'
        response = requests.get(url)
        data = response.json()

        if data.get('success'):
            return data
        return {"message": "subscription might have expired"}
