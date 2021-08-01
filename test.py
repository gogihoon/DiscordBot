import json
import requests

req = requests.get("http://ddragon.leagueoflegends.com/cdn/11.15.1/data/ko_KR/champion.json")
loadJson=req.json()
data=loadJson['data']
d = {v['key']: h for h, v in data.items()}
print(data[d['35']]['name'])
