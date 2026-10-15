# Git / GitHub 가이드

## 목차

1. [개요](#개요)
2. [기본 명령](#기본-명령)
3. [SSH 연결과 최초 업로드](#ssh-연결과-최초-업로드)
4. [상세 작업 흐름](#상세-작업-흐름)
5. [실습 및 트러블슈팅](#실습-및-트러블슈팅)
6. [체크리스트](#체크리스트)

## 개요

Git은 프로젝트 변경 이력을 관리하고 GitHub는 원격 저장소를 제공하는 서비스입니다. 터미널의 공통 이동·파일 생성·편집 명령은 [Linux/Ubuntu 문서](linux_ubuntu.md)를 참고합니다.

## 기본 명령

| 작업 | 명령 |
|---|---|
| 저장소 상태 확인 | `git status` |
| 변경 파일 스테이징 | `git add .` |
| 커밋 생성 | `git commit -m "메시지"` |
| 원격 저장소 확인 | `git remote -v` |
| 원격 저장소 주소 변경 | `git remote set-url origin 주소` |
| 원격 변경 가져오기 | `git pull origin main` |
| 업로드 | `git push origin main` |

일반적인 변경 저장 흐름은 다음과 같습니다.

```bash
git status
git add .
git commit -m "변경 내용 요약"
git push
```

## SSH 연결과 최초 업로드

### 1. SSH 키 생성

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

기본 경로를 사용하려면 안내가 나올 때 Enter를 누릅니다. 기본 공개키 경로는 `~/.ssh/id_ed25519.pub`입니다.

### 2. SSH 에이전트 시작 및 키 등록

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### 3. 공개 키를 GitHub에 등록

```bash
cat ~/.ssh/id_ed25519.pub
```

출력된 공개 키를 복사해 GitHub의 **Settings → SSH and GPG keys → New SSH key**에 등록합니다. 공개 키(`.pub`)를 등록하며 개인키 파일은 공유하지 않습니다.

### 4. 연결 확인

```bash
ssh -T git@github.com
```

성공하면 다음과 비슷한 인증 메시지가 출력됩니다.

```text
Hi <GitHub_ID>! You've successfully authenticated...
```

### 5. 로컬 프로젝트 연결 및 최초 업로드

프로젝트 디렉터리에서 Git을 초기화합니다.

```bash
git init
git remote add origin git@github.com:<GitHub_ID>/<Repository>.git
git remote -v
git add .
git commit -m "Initial commit"
git branch -M main
git push -u origin main
```

`<GitHub_ID>`와 `<Repository>`는 실제 계정과 저장소 이름으로 바꿉니다.

### 이후 작업

```bash
git add .
git commit -m "Commit message"
git pull origin main
git push origin main
```

변경이 없는 새 로컬 작업이면 pull을 먼저 할 필요가 없는 경우도 있지만, 원격 저장소와 함께 작업할 때는 업로드 전에 최신 상태를 확인합니다.

## 상세 작업 흐름

### 저장소 디렉터리 예시

```text
~/Git
├── TIL
├── SpartaPA
└── Project
```

`Git`은 상위 폴더의 이름일 뿐이며, `TIL`과 `SpartaPA`는 각각 독립 저장소가 될 수 있습니다. 각 저장소에는 별도의 `.git` 디렉터리가 있습니다.

### 여러 원격 저장소

원격 주소를 확인합니다.

```bash
git remote -v
```

`origin`의 주소를 바꾸려면 다음과 같이 합니다.

```bash
git remote set-url origin 주소
```

ROS2 실습에서 원본 기록상 두 원격에 푸시한 명령은 다음과 같습니다.

```bash
git push origin main && git push sparta main
```

`sparta`는 사전에 추가된 원격 이름이어야 합니다.

## 실습 및 트러블슈팅

### GitHub Push Protection이 API 키 커밋을 차단하는 경우

원본 실습 기록에서는 `GCP API Key Bound to a Service Account` 오류로 push가 차단됐습니다. ROS 2의 `colcon build` 과정에서 만들어진 `build/`, `install/`, `log/` 안에 터미널 환경 변수의 GCP API 키가 기록되고, `.gitignore` 규칙 문제로 해당 파일이 커밋에 포함된 것이 원인이었습니다.

ROS 2 빌드 산출물은 저장소에 넣지 않도록 `.gitignore`에 다음 패턴을 둡니다. 들여쓰기 공백 없이 각 패턴을 줄의 시작에 둡니다.

```gitignore
# ROS 2 Build / Install / Log outputs
build/
install/
log/
**/ROS2_WS/build/
**/ROS2_WS/install/
**/ROS2_WS/log/
workspace/ROS2_WS/build/
workspace/ROS2_WS/install/
workspace/ROS2_WS/log/
```

기록된 해결 과정은 이전 정상 커밋으로 되돌린 뒤 인덱스를 정리하고, 소스만 다시 스테이징·커밋해 푸시하는 방식이었습니다.

```bash
git reset --soft <이전_정상_커밋>
git reset
git add .
git commit -m "add: ROS2 예제 패키지 및 문서 추가"
git push origin main && git push sparta main
```

Push Protection은 이미 커밋된 비밀값을 찾아 차단할 수 있으므로, `.gitignore`만 추가하는 것으로 기존 커밋의 비밀값이 제거되지는 않습니다. 실제 비밀키가 노출된 경우에는 키를 폐기·교체하고, 원격에 남은 이력을 정리해야 합니다. 이력 재작성은 협업 저장소에 영향을 줄 수 있으므로 대상 커밋과 원격 상태를 확인한 뒤 적용합니다.

### 자주 쓰는 TIL 저장 순서

1. 파일을 편집합니다. 편집 방법은 [Linux/Ubuntu 문서](linux_ubuntu.md#nano-편집)를 참고합니다.
2. `git status`로 변경 내용을 확인합니다.
3. `git add .`로 추가합니다.
4. `git commit -m "메시지"`로 저장합니다.
5. `git push`로 GitHub에 업로드합니다.

## 체크리스트

- [ ] SSH 공개 키를 GitHub에 등록하고 `ssh -T`로 연결을 확인했다.
- [ ] `git remote -v`에서 원격 주소가 맞는지 확인했다.
- [ ] 커밋 전 `git status`와 포함 파일을 확인했다.
- [ ] 비밀키와 ROS 2 빌드 산출물이 커밋에 포함되지 않았는지 확인했다.
- [ ] push 차단 시 키를 폐기·교체하고 저장소 이력까지 점검했다.
