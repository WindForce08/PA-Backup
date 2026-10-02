# 대화 요약: RealSense OpenCV 데모

## 프로젝트와 파일

- 프로젝트 위치: `opencv/`
- `test.py`: RealSense 장치를 검색하고 컬러 프레임 1장을 읽어 장치 정보와 배열 크기를 출력하는 연결 확인 스크립트.
- `test2.py`: 컬러·깊이 프레임을 실시간 표시하고, 컬러 창의 마우스 위치 주변 깊이로 3D 좌표와 직선거리를 계산해 표시하는 스크립트.
- 상세 코드 분석 노트: [`opencv_test2_analysis.md`](opencv_test2_analysis.md)

## 의존성과 Python 환경

가상환경은 `opencv/.venv`이고, 루트의 `requirements.txt`에 적힌 패키지를 설치했다.

- `opencv-python==5.0.0.93`
- `numpy==2.5.3`
- `matplotlib==3.11.2`
- `pyrealsense2==2.58.4.10922`도 가상환경에 설치되어 있음

처음 `python3`로 실행했을 때 `cv2`와 `pyrealsense2`를 찾지 못했고, 패키지 설치 시 PEP 668의 externally-managed 오류도 발생했다. 원인은 `python3`가 가상환경이 아닌 시스템 Python을 가리킨 것이었다. 가상환경의 실행 파일을 직접 지정해 해결했다.

## 확인된 실행 결과

`opencv/` 폴더에서 다음 명령으로 `test.py` 실행이 성공했다.

```bash
./.venv/bin/python3 test.py
```

출력된 장치는 RealSense D435이며, 컬러 프레임 크기는 `(480, 640, 3)`이었다. 이 크기는 영상 해상도와 채널 수이므로 장애물이 있어도 바뀌지 않는다. `test.py`는 장애물의 거리나 픽셀값을 출력하는 프로그램이 아니다.

현재 터미널 상태에는 다음 `test2.py` 실행도 종료 코드 0으로 기록되어 있다.

```bash
./.venv/bin/python3 test2.py
```

이 스크립트는 컬러 창에서 마우스를 움직여 측정 위치를 선택하며, `q` 키로 종료한다.

## `test2.py`의 좌표 계산 개요

깊이 프레임을 컬러 좌표계로 정렬한 후, 마우스 주변 최대 10×10 ROI에서 0이 아닌 0.2~3.0m 범위의 깊이만 유효 샘플로 선택한다. 유효 샘플이 ROI의 30% 이상이면 중앙값을 미터 단위로 변환한다.

- `Z`: 카메라 앞쪽 깊이
- `X = (u - ppx) × Z / fx`: 영상 가로 방향 좌표
- `Y = (v - ppy) × Z / fy`: 영상 세로 방향 좌표
- `Distance = sqrt(X² + Y² + Z²)`: 카메라 원점부터 점까지의 직선거리

ROI 중앙값을 사용하므로 물체 경계를 포함하면 커서 한 픽셀의 깊이와 다를 수 있다. 또한 좌표 계산은 핀홀 카메라 모델을 사용하므로 정밀 측정 시 렌즈 왜곡과 컬러·깊이 좌표계 관계를 검증해야 한다.

## 실행 명령

`opencv/` 폴더에서 실행할 때:

```bash
./.venv/bin/python3 test.py
./.venv/bin/python3 test2.py
```

루트(`/home/pa31/GIT/.workspace`)에서 실행할 때:

```bash
opencv/.venv/bin/python3 opencv/test.py
opencv/.venv/bin/python3 opencv/test2.py
```

가상환경 활성화 여부가 불확실할 때는 위처럼 가상환경 인터프리터의 경로를 직접 사용하는 것이 확실하다. `python3`가 어느 인터프리터를 가리키는지 확인하려면 `command -v python3` 또는 `python3 -c "import sys; print(sys.executable)"`를 사용한다.
