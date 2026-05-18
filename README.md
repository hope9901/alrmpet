# alrmpet

명령어 앞에 `alrmpet`만 붙이면 실행 완료 시 알림을 받을 수 있습니다.
Linux의 `time` 명령어처럼 동작합니다.

```bash
alrmpet python train.py --epochs 100
alrmpet bash long_script.sh
alrmpet make build
```

## 설치

```bash
git clone https://github.com/hope9901/alrmpet.git
cd alrmpet
pip install -e .
```

## 사용법

```bash
# 기본 사용 - 명령어 앞에 alrmpet 붙이기
alrmpet sleep 10
alrmpet python train.py --epochs 100

# 특정 사람에게 이메일 알림 (이니셜 지정)
alrmpet --to hyg python train.py
alrmpet --to hyg,kjw python train.py     # 여러 명
alrmpet --to all python train.py         # 전체

# 캐릭터 변경
alrmpet --character fireball -- python train.py

# 실행 중인 프로세스 감시
alrmpet --watch-pid 12345

# Screen 세션 감시
alrmpet --watch-screen my_training

# 설정 파일 생성
alrmpet --init

# 알림 테스트
alrmpet --test
```

## 펫 캐릭터

Codex 스타일의 ANSI 컬러 ASCII 펫이 작업 완료 후 결과를 보여줍니다.

| 캐릭터 | 테마 | 일할 때 | 성공 |
|--------|------|---------|------|
| `codex` | 파란 코더 | `~ coding...` | `\(^o^)/ Done!` |
| `dewey` | 주황 오리 | `>(oo)>` 좌우이동 | `QUACK!!` |
| `fireball` | 빨간 불꽃 | `~ burn!` | `FIRE!!` |
| `rocky` | 회색 바위 | `~ grind` | `ROCK!` |
| `seedy` | 초록 새싹 | `~ grow` | `BLOOM!` |

```bash
alrmpet --character dewey -- python train.py
```

## 이메일 수신자 선택 (`--to`)

config에 이니셜과 이메일을 등록하고, `--to`로 선택합니다.

```yaml
# ~/.config/alrmpet/config.yaml
notification:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    use_tls: true
    username: "sender@gmail.com"
    password: "앱비밀번호"       # Google 앱 비밀번호
    from_addr: "sender@gmail.com"
    recipients:
      hyg: "hyg@gmail.com"
      kjw: "kjw@university.ac.kr"
      lsh: "lsh@gmail.com"
```

| 명령어 | 동작 |
|--------|------|
| `alrmpet --to hyg python train.py` | hyg에게만 이메일 |
| `alrmpet --to hyg,kjw python train.py` | hyg, kjw에게 이메일 |
| `alrmpet --to all python train.py` | 전체에게 이메일 |
| `alrmpet python train.py` | 이메일 안 보냄 |

> **Gmail 앱 비밀번호**: Google 계정 > 보안 > 2단계 인증 > 앱 비밀번호에서 생성

## 원격 알림 (외부 IP)

### 방법 1: 직접 HTTP 푸시

수신 컴퓨터에서 리시버를 실행하고, 발신 컴퓨터에서 IP를 설정합니다.

```bash
# 수신 컴퓨터 (알림 받을 곳)
alrmpet --listen 9922
```

```yaml
# 발신 컴퓨터 config.yaml
notification:
  remote:
    enabled: true
    host: "수신컴퓨터IP"
    port: 9922
```

### 방법 2: ntfy.sh (휴대폰/브라우저 푸시)

```yaml
# config.yaml
notification:
  ntfy:
    enabled: true
    topic: "my-alrmpet-alerts"
    server: "https://ntfy.sh"
```

휴대폰에 [ntfy 앱](https://ntfy.sh)을 설치하고 같은 토픽을 구독하면 푸시 알림을 받습니다.

## 알림 채널 요약

| 채널 | 설명 | 설정 |
|------|------|------|
| Pet | 터미널 ASCII 펫 배너 | 기본 활성화 |
| Email | SMTP 이메일 (`--to` 필수) | config.yaml |
| Webhook | Discord / Slack | config.yaml |
| ntfy | 휴대폰/브라우저 푸시 | config.yaml |
| Remote | 외부 IP HTTP 푸시 | config.yaml + `--listen` |
| Desktop | notify-send (Linux) | 기본 활성화 |
| Sound | 터미널 벨 | 기본 활성화 |

## 전체 옵션

| 옵션 | 설명 |
|------|------|
| `--to NAMES` | 이메일 수신자 (이니셜, 쉼표 구분, 또는 `all`) |
| `--character NAME` | 펫 캐릭터 (`codex`, `dewey`, `fireball`, `rocky`, `seedy`) |
| `--no-pet` | 펫 비활성화 |
| `--no-email` | 이메일 비활성화 |
| `--no-desktop` | 데스크톱 알림 비활성화 |
| `--no-sound` | 터미널 벨 비활성화 |
| `--no-webhook` | 웹훅 비활성화 |
| `--no-ntfy` | ntfy 비활성화 |
| `--no-remote` | 원격 푸시 비활성화 |
| `-c`, `--config PATH` | 설정 파일 경로 |
| `--watch-pid PID` | 실행 중인 프로세스 PID 감시 |
| `--watch-screen NAME` | Screen 세션 감시 |
| `--listen PORT` | 원격 알림 리시버 시작 |
| `-V`, `--version` | 버전 출력 |
| `-h`, `--help` | 도움말 |

## 실전 예시

```bash
# Screen에서 학습 돌리고 알림 받기
screen -S training
python train_model.py --epochs 1000
# Ctrl+A, D 로 detach 후:
alrmpet --watch-screen training

# 긴 작업 + hyg에게 이메일
alrmpet --to hyg --character fireball -- python analysis.py

# SSH 원격 서버에서 (펫/데스크톱 없이 이메일만)
alrmpet --to all --no-pet --no-desktop -- bash backup.sh
```
