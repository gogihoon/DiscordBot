# DiscordBot

디스코드에서 음악 재생, 롤(LoL) 정보, 날씨, 스팀 게임 가격 등 다양한 기능을 제공하는 봇입니다.

---

## 1. 주요 기능

- `/join` : 음성 채널에 연결
- `/quit` : 음성 채널에서 나가기
- `/add` : 대기열에 음악 추가
- `/queue` : 대기열 확인
- `/skip` : 음악 스킵
- `/pause` : 음악 일시정지/재개
- `/volume` : 볼륨 변경
- `/weather` : 날씨 확인
- `/steam` : 스팀 게임 가격 확인
- `/tier` : 롤 소환사 랭크 정보 확인
- `/most` : 롤 소환사의 모스트 챔피언 확인

---

## 2. 폴더 구조

```
DiscordBot/
│
├── api_keys.json         # API 키 파일 (직접 생성 필요)
├── config.py             # API 키 및 공통 설정
├── lol.py                # 롤(LoL) 관련 기능
├── main.py               # 봇 실행 메인 파일
├── music.py              # 음악 재생 기능
├── steam.py              # 스팀 게임 가격 기능
├── weather.py            # 날씨 기능
├── README.md             # 이 파일
└── .gitignore
```

---

## 3. 설치 및 준비

### 필수 라이브러리 설치

아래 명령어로 필요한 패키지를 설치하세요.

```bash
pip install beautifulsoup4 discord.py[voice] ffmpeg PyNaCl requests yt_dlp html5lib
```

### API 키 준비

`api_keys.json` 파일을 프로젝트 폴더에 아래와 같이 생성하세요.

```json
{
  "riot_key": "여기에_라이엇_API_키",
  "discord_key": "여기에_디스코드_봇_키",
  "beta_key": "여기에_베타_봇_키"
}
```

---

## 4. 실행 방법

터미널에서 프로젝트 폴더로 이동 후 아래 명령어를 실행하세요.

```bash
python main.py
```

---

## 5. 명령어 예시

- `/add [노래제목 또는 유튜브URL]` : 음악 대기열에 추가
- `/queue` : 현재 대기열 확인
- `/tier [소환사명] [태그]` : 롤 랭크 티어 확인
- `/most [소환사명] [태그]` : 롤 모스트 챔피언 확인
- `/weather [지역명]` : 해당 지역의 날씨 확인
- `/steam [게임명]` : 스팀 게임 가격 확인

---

## 6. 참고

- 봇을 서버에 초대할 때는 음성/메시지 권한이 필요합니다.
- 각 기능별 코드는 `music.py`, `lol.py`, `weather.py`, `steam.py`에 분리되어 있습니다.
- 추가 기능은 각 파일에 함수로 구현 후, `main.py`에서 등록하면 됩니다.

---

## 7. 문의

오류나 문의사항은 이슈로 남겨주세요.