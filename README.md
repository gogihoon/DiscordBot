# 🚀 DiscordBot - All-in-One Discord Entertainment Bot 🎶🎮

<p align="center">
  <img src="https://img.shields.io/github/languages/top/gogihoon/DiscordBot?style=flat-square">
  <img src="https://img.shields.io/github/license/gogihoon/DiscordBot?style=flat-square">
  <img src="https://img.shields.io/github/stars/gogihoon/DiscordBot?style=flat-square">
</p>

<p align="center">
  <img src="https://i.imgur.com/KBfn8V8.png" width="120" alt="DiscordBot Logo"/>
</p>

> **음악 · 게임 · 날씨 · 정보**  
> 기능이 많아용~

---

## ✨ 주요 명령어

| 커맨드                      | 기능 설명                                   |
|-----------------------------|---------------------------------------------|
| `/join`                     | 음성 채널에 봇 연결                        |
| `/quit`                     | 음성 채널에서 봇 나가기                    |
| `/add`                      | 음악 대기열에 추가                         |
| `/queue`                    | 현재 음악 대기열 보기                      |
| `/skip`                     | 다음 노래로 넘기기                         |
| `/pause`                    | 음악 일시정지/재생                         |
| `/volume`                   | 볼륨 조절                                  |
| `/weather [지역명]`         | 해당 지역의 실시간 날씨 확인               |
| `/steam [게임명]`           | 스팀 게임 가격 검색                        |
| `/tier [소환사명] [태그]`   | 롤 소환사 랭크 조회                        |
| `/most [소환사명] [태그]`   | 롤 소환사의 모스트 챔피언 TOP3              |

---

## 🗂️ 폴더 구조

```
DiscordBot/
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

## ⚡️ 빠른 시작

### 1. 필수 라이브러리 설치

```bash
pip install beautifulsoup4 discord.py[voice] ffmpeg PyNaCl requests yt_dlp html5lib
```

### 2. API 키 등록

프로젝트 폴더에 `api_keys.json` 아래 형식으로 생성:

```json
{
  "riot_key": "여기에_라이엇_API_키",
  "discord_key": "여기에_디스코드_봇_키",
  "beta_key": "여기에_베타_봇_키"
}
```

### 3. 실행

```bash
python main.py
```

---

## 👀 스크린샷

<p align="center">
  <img src="https://i.imgur.com/jmu6tXm.png" width="350" alt="음악봇 스크린샷"/>
</p>

---

## 💡 참고사항

- **권한**: 봇을 초대할 때 "음성" 및 "메시지" 권한을 꼭 부여하세요.
- **모듈 구조**: 기능별로 `music.py`, `lol.py`, `weather.py`, `steam.py`에 코드가 분리되어 있습니다.
- **확장성**: 새로운 기능을 추가하려면 해당 파일에 함수를 만들고, `main.py`에서 등록하면 됩니다.

---