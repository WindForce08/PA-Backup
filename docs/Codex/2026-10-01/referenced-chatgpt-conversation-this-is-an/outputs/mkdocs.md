# MkDocs 및 GitHub TIL 관리 가이드

## 목차

1. [개요](#개요)
2. [기본 명령](#기본-명령)
3. [가상 환경](#가상-환경)
4. [상세 설명과 운영 규칙](#상세-설명과-운영-규칙)
5. [실습 및 트러블슈팅](#실습-및-트러블슈팅)
6. [체크리스트](#체크리스트)

## 개요

MkDocs는 Markdown 파일을 문서 사이트로 빌드하고 미리 볼 수 있게 해줍니다. 공통 셸 명령은 [Linux/Ubuntu 문서](linux_ubuntu.md), Git 저장·업로드 명령은 [Git/GitHub 문서](git_github.md)에 정리되어 있습니다.

## 기본 명령

```bash
mkdocs new .
mkdocs serve
mkdocs build
mkdocs --version
```

| 명령 | 설명 |
|---|---|
| `mkdocs new .` | 현재 디렉터리에 MkDocs 프로젝트 생성 |
| `mkdocs serve` | 개발 서버를 실행해 문서를 미리 보기 |
| `mkdocs build` | 사이트 파일 빌드 |
| `mkdocs --version` | 설치 버전 확인 |

## 가상 환경

```bash
python3 -m venv venv
source venv/bin/activate
deactivate
```

- 생성: `python3 -m venv venv`
- 활성화: `source venv/bin/activate`
- 종료: `deactivate`

## 상세 설명과 운영 규칙

원본 저장소 구조 예시는 다음과 같습니다.

```text
~/Git
├── TIL
├── SpartaPA
└── Project
```

`Git`은 상위 폴더이며 `TIL`과 `SpartaPA`는 각각 독립적인 Git 저장소입니다. 저장소별 `.git` 디렉터리가 따로 있습니다.

원본의 개인 규칙:

- 파일명은 영어로 작성한다.
- 폴더명은 소문자를 사용한다.
- 공백 대신 언더바(`_`)를 사용한다.
- 하루에 하나 이상의 문서를 작성한다.

## 실습 및 트러블슈팅

### 프로젝트 시작 예시

```bash
mkdir -p ~/Git/TIL
cd ~/Git/TIL
python3 -m venv venv
source venv/bin/activate
mkdocs new .
mkdocs serve
```

프로젝트에 따라 이미 MkDocs 설정 파일이 있으면 `mkdocs new .` 대신 `mkdocs serve`로 바로 확인합니다.

### 자주 필요한 설치 명령

원본에서 안내한 패키지 설치 명령입니다.

```bash
sudo apt install tree
sudo apt install python3-venv
pip install 패키지명
```

- `tree`: 디렉터리 구조를 트리 형태로 확인할 때 설치합니다.
- `python3-venv`: Python 가상 환경 기능을 설치합니다.
- Python 패키지는 프로젝트 가상 환경을 활성화한 뒤 `pip install 패키지명`으로 설치하는 것을 권장합니다.

### GitHub 업로드

저장소 상태 확인, 파일 추가, 커밋, push, SSH 연결은 [Git/GitHub 가이드](git_github.md)를 기준 문서로 사용합니다. 이 문서에는 원본에서 중복된 Git 명령 전체를 반복하지 않고 해당 절차로 연결합니다.

## 체크리스트

- [ ] 프로젝트 가상 환경을 만들고 활성화했다.
- [ ] `mkdocs serve`로 미리 보기를 확인했다.
- [ ] `mkdocs build`가 성공하는지 확인했다.
- [ ] 파일명, 폴더명, 공백 사용 규칙을 적용했다.
- [ ] GitHub 업로드 절차는 [Git/GitHub 문서](git_github.md)를 따랐다.
