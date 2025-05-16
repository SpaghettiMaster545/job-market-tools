import requests

params = {
    'page': 2,
    'sortBy': 'published',
    'orderBy': 'DESC',
    'perPage': 100,
    'salaryCurrencies': 'PLN'
}
headers = {
    'Accept': 'application/json',
    'version': '2'
}

resp = requests.get('https://api.justjoin.it/v2/user-panel/offers',
                    params=params,
                    headers=headers)
resp.raise_for_status()
data = resp.json()
print(data)
