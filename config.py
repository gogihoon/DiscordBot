import json
import logging
import os

from dotenv import load_dotenv

import logconf

# 다른 모듈이 로그를 남기기 전에 먼저 설정한다.
logconf.setup()
log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 실제 환경변수가 있으면 그 값이 우선하고, 없으면 .env 파일에서 읽는다.
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _load_legacy_keys():
    """예전 방식인 api_keys.json이 남아 있으면 보조로 읽어 둔다."""
    path = os.path.join(BASE_DIR, "api_keys.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        log.warning("api_keys.json을 읽지 못했어요: %s", e)
        return {}


_legacy = _load_legacy_keys()


def _get_key(env_name, legacy_name):
    value = os.getenv(env_name) or _legacy.get(legacy_name)
    if not value:
        log.warning("%s 이(가) 없어요. 관련 기능이 동작하지 않아요.", env_name)
        return ""
    return value


RIOT_KEY = _get_key("RIOT_KEY", "riot_key")
DISCORD_KEY = _get_key("DISCORD_KEY", "discord_key")
BETA_KEY = _get_key("BETA_KEY", "beta_key")
GEMINI_KEY = _get_key("GEMINI_KEY", "gemini_key")
