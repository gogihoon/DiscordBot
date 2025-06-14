import json
import requests

with open("api_keys.json", "r") as f:
    key = json.load(f)

RIOT_KEY = key.get("riot_key")
DISCORD_KEY = key.get("discord_key")
BETA_KEY = key.get("beta_key")
GEMINI_KEY = key.get("gemini_key")

# 롤 버전 정보
ver_res = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
lol_version = ver_res.json()
