"""로깅 설정.

다른 모듈이 로그를 남기기 전에 설정되도록 config.py 맨 위에서 불러 쓴다.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "bot.log")


def setup(level=logging.INFO):
    root = logging.getLogger()
    if root.handlers:
        # 이미 설정했으면 다시 붙이지 않는다.
        return

    handlers = [logging.StreamHandler()]
    try:
        handlers.append(
            RotatingFileHandler(
                LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
            )
        )
    except OSError as e:
        print(f"[logconf] 로그 파일을 열지 못해 콘솔에만 남겨요: {e}")

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )
