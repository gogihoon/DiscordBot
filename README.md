

<p align="center">
  <img src="https://imgur.com/jmu6tXm.png" width="120" alt="DiscordBot Logo"/>
</p>

> **음악 · 게임 · 날씨 · 정보**  
> 개발중...

---

## 주요 명령어

| 커맨드                      | 기능 설명                                   |
|-----------------------------|---------------------------------------------|
| `/join`                     | 음성 채널에 봇 연결                        |
| `/quit`                     | 음성 채널에서 봇 나가기                    |
| `/add [노래 제목 또는 URL]` | 음악 대기열에 추가                         |
| `/queue`                    | 현재 음악 대기열 보기                      |
| `/skip`                     | 다음 노래로 넘기기                         |
| `/pause`                    | 음악 일시정지/재생                         |
| `/volume [0-100]`           | 볼륨 조절 (다음 곡에도 유지)               |
| `/weather [지역명]`         | 해당 지역의 실시간 날씨 확인               |
| `/steam [게임명]`           | 스팀 게임 가격 검색                        |
| `/tier [소환사명] [태그]`   | 롤 소환사 랭크 조회                        |
| `/most [소환사명] [태그]`   | 롤 소환사의 모스트 챔피언 TOP3              |
| `/ask [질문]`               | Gemini AI에게 질문                         |

---

## 폴더 구조

```
DiscordBot/
├── .env                  # API 키 (직접 생성, 커밋되지 않음)
├── .env.example          # 키 양식 템플릿
├── requirements.txt      # 파이썬 의존성
├── config.py             # API 키 로딩
├── logconf.py            # 로깅 설정
├── utils.py              # 공용 응답/임베드 헬퍼
├── gemini.py             # Gemini AI 기능
├── lol.py                # 롤(LoL) 관련 기능
├── main.py               # 봇 실행 메인 파일
├── music.py              # 음악 재생 기능
├── steam.py              # 스팀 게임 가격 기능
├── weather.py            # 날씨 기능
├── README.md             # 이 파일
└── .gitignore
```

---

## 시작

### 1. 필수 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 1-1. ffmpeg 설치 (음악 기능에 필수)

**`pip install ffmpeg`로는 설치되지 않습니다.** PyPI의 `ffmpeg` 패키지는 실제 인코더가
아니라 껍데기라서, ffmpeg 실행 파일을 직접 받아 `PATH`에 등록해야 음악이 재생됩니다.

- **Windows**: [gyan.dev 빌드](https://www.gyan.dev/ffmpeg/builds/)를 받아 압축을 풀고
  `bin` 폴더를 시스템 환경변수 `Path`에 추가 (예: `C:\ffmpeg\bin`)
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`

설치 확인:

```bash
ffmpeg -version
```

### 2. API 키 등록

`.env.example`을 `.env`로 복사한 뒤 값을 채웁니다.

```env
DISCORD_KEY=여기에_디스코드_봇_키
BETA_KEY=여기에_베타_봇_키
RIOT_KEY=여기에_라이엇_API_키
GEMINI_KEY=여기에_Gemini_API_키
```

시스템 환경변수로 설정한 값이 `.env`보다 우선합니다. 서버에 올릴 때는 파일 없이
환경변수만으로도 동작합니다. 예전 방식인 `api_keys.json`이 남아 있으면 보조로 계속 읽습니다.

### 3. 실행

```bash
python main.py
```

---

## 참고사항

- **권한**: 봇을 초대할 때 "음성" 및 "메시지" 권한을 꼭 부여하세요.
- 이모티콘 확대 기능은 봇에게 **메시지 관리** 권한이 있는 채널에서만 동작합니다.
- 롤 이미지에 쓰는 ddragon 버전은 6시간마다 자동으로 갱신됩니다.
- 음악 명령(`/join`, `/add` 등)은 서버 안에서만 쓸 수 있습니다. 롤·날씨·스팀·AI 명령은 DM에서도 됩니다.
- 음성 채널에 사람이 아무도 남지 않으면 봇이 스스로 나갑니다.
- 로그는 콘솔과 `bot.log`에 함께 남습니다 (1MB씩 3개까지 순환).