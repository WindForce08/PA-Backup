# Linux / Ubuntu 기본 명령어

## 목차

1. [개요](#개요)
2. [기본 명령](#기본-명령)
3. [상세 설명과 예제](#상세-설명과-예제)
4. [실습 및 주의사항](#실습-및-주의사항)
5. [체크리스트](#체크리스트)

## 개요

Ubuntu 터미널에서 현재 위치를 확인하고 디렉터리와 파일을 만들고 편집하는 기본 명령을 정리합니다. `mv`는 파일과 디렉터리 이동 및 이름 변경에 모두 사용합니다.

## 기본 명령

| 작업 | 명령 |
|---|---|
| 현재 경로 확인 | `pwd` |
| 파일 목록 확인 | `ls` |
| 디렉터리 이동 | `cd 경로` |
| 상위 디렉터리 이동 | `cd ..` |
| 홈 디렉터리 이동 | `cd ~` |
| 디렉터리 생성 | `mkdir 디렉터리명` |
| 중간 경로까지 생성 | `mkdir -p 상위/하위` |
| 빈 파일 생성 | `touch 파일명` |
| 파일 편집 | `nano 파일명` |
| 파일·디렉터리 이동/이름 변경 | `mv 원본 목적지` |

## 상세 설명과 예제

### 경로 이동과 확인

```bash
pwd
ls
cd 폴더명
cd ..
cd ~
```

### 디렉터리와 파일 만들기

```bash
mkdir notes
mkdir -p projects/ros2/src
touch notes/today.md
```

### nano 편집

```bash
nano 파일명.md
```

| 동작 | 키 |
|---|---|
| 저장 메뉴 | `Ctrl + O` |
| 저장할 파일명 확인 | `Enter` |
| 종료 | `Ctrl + X` |
| 현재 줄 잘라내기 | `Ctrl + K` |
| 붙여넣기 | `Ctrl + U` |
| 검색 | `Ctrl + W` |

### `mv`로 디렉터리 이동 및 이름 변경

기본 형식은 다음과 같습니다.

```bash
mv 원본디렉터리 목적지
```

디렉터리를 다른 곳으로 이동합니다.

```bash
mv ~/test ~/Documents/
```

같은 위치에서 이름을 변경합니다.

```bash
mv test test_backup
```

이동하면서 이름도 바꿉니다. 목적지의 상위 디렉터리는 이미 존재해야 합니다.

```bash
mv ~/test ~/Documents/test_backup
```

여러 디렉터리를 한 위치로 이동합니다.

```bash
mv dir1 dir2 dir3 ~/Documents/
```

권한이 필요한 위치에서는 `sudo`가 필요할 수 있습니다.

```bash
sudo mv /원본/디렉터리 /목적지/
```

예를 들어 `/home/pa31/test`를 `/opt/`로 옮기는 명령은 다음과 같습니다.

```bash
sudo mv /home/pa31/test /opt/
```

`mv`는 Move의 약자이며 파일에도 사용할 수 있습니다. 폴더 이름 변경은 같은 디렉터리 안에서 원래 이름을 새 이름으로 옮기는 동작입니다.

```bash
mv old_name new_name
```

## 실습 및 주의사항

```bash
pwd
mkdir -p ~/practice/docs
touch ~/practice/docs/first.md
mv ~/practice/docs/first.md ~/practice/docs/intro.md
ls ~/practice/docs
```

- `mv` 대상 경로에 같은 이름의 파일이나 디렉터리가 있으면 기존 항목에 들어가거나 덮어쓰기가 발생할 수 있으니 목적지를 먼저 확인합니다.
- `sudo mv`는 시스템 경로에서만 신중하게 사용합니다.
- `mkdir -p`는 필요한 상위 경로도 함께 만듭니다.

## 체크리스트

- [ ] `pwd`, `ls`로 현재 위치와 항목을 확인했다.
- [ ] 올바른 위치에서 `mkdir`, `touch`를 실행했다.
- [ ] `nano`에서 저장 후 종료하는 방법을 확인했다.
- [ ] `mv`의 원본과 목적지 경로를 확인했다.
