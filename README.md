# alrmpet 🐱

명령어 앞에 `alrmpet`만 붙이면 실행 완료 시 알림을 받을 수 있습니다.
Linux의 `time` 명령어처럼 동작합니다.

```bash
# time 처럼 사용
alrmpet python train.py --epochs 100
alrmpet bash long_script.sh
alrmpet make build
```

## 설치

```bash
cd alrmpet
pip install -e .
```

## 사용법

```bash
# 기본 사용 — 명령어 앞에 alrmpet 붙이기
alrmpet sleep 10
alrmpet python train.py --epochs 100

# 캐릭터 변경 (-- 로 구분)
alrmpet --character dog -- python train.py

# 실행 중인 프로세스 감시
alrmpet --watch-pid 12345

# Screen 세션 감시
alrmpet --watch-screen my_training

# 설정 파일 생성
alrmpet --init

# 알림 테스트
alrmpet --test
```

## 알림 채널

| 채널 | 설명 | 설정 필요 |
|------|------|-----------|
| 🐱 Pet | 터미널 ASCII 펫 애니메이션 | 없음 |
| 📧 Email | SMTP 이메일 | config.yaml |
| 💬 Webhook | Discord/Slack | config.yaml |
| 🖥 Desktop | notify-send | 없음 |
| 🔔 Sound | 터미널 벨 | 없음 |

## 설정

```bash
alrmpet --init  # ~/.config/alrmpet/config.yaml 생성
```

설정 파일에서 이메일, 웹훅 등을 활성화할 수 있습니다.

## 옵션

| 옵션 | 설명 |
|------|------|
| `--character {cat,dog,robot,bird}` | 펫 캐릭터 |
| `--no-pet` | 펫 비활성화 |
| `--no-email` | 이메일 비활성화 |
| `--no-desktop` | 데스크톱 알림 비활성화 |
| `--no-sound` | 소리 비활성화 |
| `-c`, `--config` | 설정 파일 경로 |
| `--watch-pid PID` | PID 감시 |
| `--watch-screen NAME` | Screen 세션 감시 |
