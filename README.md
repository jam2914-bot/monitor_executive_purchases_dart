# 📊 OpenDart API 기반 임원 매수 모니터링 봇

OpenDart API를 활용하여 임원ㆍ주요주주 특정증권등 소유상황보고서를 실시간 모니터링하고, 장내매수 정보를 텔레그램으로 알림받는 GitHub Actions 기반 자동화 봇입니다.

## 🚀 주요 기능

- ✅ **OpenDart API 기반**: 안정적이고 공식적인 데이터 소스 활용
- ✅ **실시간 모니터링**: 하루 5회 자동 실행으로 실시간성 확보
- ✅ **장내매수 감지**: 임원 매수 거래 자동 탐지 및 분석
- ✅ **텔레그램 알림**: 즉시 알림으로 투자 기회 놓치지 않음
- ✅ **중복 방지**: 동일 공시 중복 알림 방지 시스템
- ✅ **상세 로깅**: 모든 과정 기록으로 문제 해결 용이
- ✅ **GitHub Actions**: 무료 클라우드 환경에서 24/7 자동 실행

## 📋 시스템 요구사항

- GitHub 계정
- OpenDart API 키 (무료)
- 텔레그램 봇 토큰 및 채팅 ID

## 🔧 설정 방법

### 1. OpenDart API 키 발급

1. [OpenDart 홈페이지](https://opendart.fss.or.kr/) 접속
2. 회원가입 및 로그인
3. `인증키 신청/관리` 메뉴 클릭
4. 인증키 신청 (즉시 발급)
5. 발급받은 API 키 복사 보관

### 2. 텔레그램 봇 생성

1. 텔레그램에서 `@BotFather` 검색
2. `/newbot` 명령어 입력
3. 봇 이름 및 사용자명 설정
4. 발급받은 **Bot Token** 복사 보관

### 3. 텔레그램 채팅 ID 확인

1. 생성한 봇과 대화 시작 (아무 메시지나 전송)
2. 브라우저에서 다음 URL 접속:
   ```
   https://api.telegram.org/bot[BOT_TOKEN]/getUpdates
   ```
3. 응답에서 `"chat":{"id":숫자}` 부분의 숫자가 채팅 ID
4. 채팅 ID 복사 보관

### 4. GitHub Repository 설정

1. 이 저장소를 Fork 또는 새 저장소 생성
2. `Settings` → `Secrets and variables` → `Actions` 클릭
3. 다음 Secrets 추가:

| Secret 이름 | 값 | 설명 |
|-------------|-----|------|
| `DART_API_KEY` | 발급받은 OpenDart API 키 | OpenDart API 인증 |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 | 텔레그램 메시지 전송 |
| `TELEGRAM_CHAT_ID` | 텔레그램 채팅 ID | 알림 수신 대상 |

### 5. 파일 업로드

다음 파일들을 저장소에 업로드:

```
your-repo/
├── .github/
│   └── workflows/
│       └── monitor.yml
├── monitor_executive_purchases_dart.py
├── requirements.txt
└── README.md
```

## 🎯 사용법

### 자동 실행 (권장)

GitHub Actions가 다음 시간에 자동 실행됩니다:

- **오전 9시** (KST)
- **오후 12시** (KST)  
- **오후 3시** (KST)
- **오후 6시** (KST)
- **오후 9시** (KST)

### 수동 실행

1. GitHub 저장소의 `Actions` 탭 클릭
2. `OpenDart Executive Purchase Monitor` 워크플로우 선택
3. `Run workflow` 버튼 클릭

### 로컬 실행

```bash
# 환경 변수 설정
export DART_API_KEY="your_dart_api_key"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_telegram_chat_id"

# 패키지 설치
pip install -r requirements.txt

# 실행
python monitor_executive_purchases_dart.py
```

## 📱 알림 예시

```
🏢 임원 장내매수 알림

📊 회사명: KZ정밀
📈 종목코드: 036560
👤 보고자: 최종태
💼 직위: 비등기임원
💰 거래유형: 장내매수
📊 주식수: 1,000주
💵 가격: 12,870원
📅 거래일: 2025-07-18
📋 접수번호: 20250718000546
📅 공시일: 20250718

⏰ 알림시간: 2025-07-18 16:30:15 KST

#임원매수 #OpenDart #장내매수
```

## 🔍 모니터링 대상

- **임원ㆍ주요주주특정증권등소유상황보고서**
- **유가증권시장** 및 **코스닥시장** 전체
- **장내매수**, **매수**, **취득** 거래 유형
- **어제~오늘** 공시 범위

## 📊 시스템 아키텍처

```
OpenDart API → 공시 데이터 수집 → 임원 공시 필터링 → 장내매수 감지 → 텔레그램 알림
     ↓              ↓                    ↓                ↓              ↓
  인증키 인증    JSON 응답 파싱      키워드 매칭        정규식 분석     메시지 포맷팅
```

## 🛠️ 기술 스택

- **Python 3.9+**: 메인 개발 언어
- **OpenDart API**: 공시 데이터 소스
- **Requests**: HTTP API 호출
- **Pandas**: 데이터 처리
- **Pytz**: 한국 시간대 처리
- **GitHub Actions**: CI/CD 및 스케줄링
- **Telegram Bot API**: 알림 전송

## 🔧 고급 설정

### 모니터링 기간 변경

`monitor_executive_purchases_dart.py` 파일에서 `days_back` 매개변수 수정:

```python
# 3일 전부터 모니터링
results = monitor.monitor_executive_purchases(days_back=3)
```

### 스케줄 변경

`.github/workflows/monitor.yml` 파일의 cron 설정 수정:

```yaml
schedule:
  # 매시간 실행
  - cron: '0 * * * 1-5'
  # 30분마다 실행  
  - cron: '*/30 * * * 1-5'
```

### 키워드 확장

`OpenDartAPI` 클래스의 `executive_keywords` 리스트 수정:

```python
executive_keywords = [
    '임원ㆍ주요주주특정증권등소유상황보고서',
    '임원·주요주주특정증권등소유상황보고서',
    '임원특정증권등소유상황보고서',
    '주요주주특정증권등소유상황보고서',
    '추가키워드'  # 필요시 추가
]
```

## 📈 성능 최적화

- **API 호출 제한**: 1초 간격으로 호출하여 서버 부하 방지
- **중복 처리 방지**: 처리된 공시 번호 추적
- **페이지네이션**: 대량 데이터 효율적 처리
- **오류 복구**: 실패 시 자동 재시도 로직
- **로그 관리**: 상세한 실행 로그 기록

## 🚨 주의사항

### 보안

- ⚠️ **API 키 노출 금지**: GitHub Secrets 사용 필수
- ⚠️ **공개 저장소 주의**: 민감 정보 커밋 금지
- ⚠️ **정기적 키 교체**: 보안을 위해 주기적으로 API 키 재발급

### 사용 제한

- OpenDart API: 분당 1,000회 호출 제한
- GitHub Actions: 월 2,000분 무료 (Public 저장소는 무제한)
- 텔레그램 봇: 초당 30개 메시지 제한

### 법적 고지

- 본 도구는 공개된 공시 정보만을 활용합니다
- 투자 결정은 본인 책임하에 이루어져야 합니다
- 공시 정보의 정확성은 원본 공시를 확인하시기 바랍니다

## 🐛 문제 해결

### 일반적인 문제

1. **API 키 오류**
   ```
   해결: GitHub Secrets에 올바른 DART_API_KEY 설정 확인
   ```

2. **텔레그램 알림 실패**
   ```
   해결: TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID 확인
   ```

3. **공시 누락**
   ```
   해결: 스케줄 빈도 증가 또는 days_back 값 증가
   ```

### 로그 확인

GitHub Actions의 `Actions` 탭에서 실행 로그 확인 가능:

```
📊 모니터링 완료

📅 조회 기간: 20250718 ~ 20250719
🔍 검색 방식: OpenDart API
📋 결과: 임원 매수 공시 2건 발견
⏰ 완료 시간: 2025-07-19 00:32:03 KST
```

## 📞 지원

- **Issues**: GitHub Issues를 통한 버그 신고 및 기능 요청
- **Discussions**: 사용법 문의 및 개선 제안
- **Wiki**: 상세한 설정 가이드 및 FAQ

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

## 🙏 기여

Pull Request와 Issue 제출을 환영합니다!

---

**⚡ 빠른 시작**: 위의 설정 방법을 따라하면 10분 내에 임원 매수 모니터링 봇을 구축할 수 있습니다!
