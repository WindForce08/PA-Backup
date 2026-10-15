# examples 프로젝트 분석

## 목차

1. [분석 범위와 요약](#1-분석-범위와-요약)
2. [프로젝트 구성](#2-프로젝트-구성)
3. [대표 실행 플로우](#3-대표-실행-플로우)
4. [단계별 실험 플로우](#4-단계별-실험-플로우)
5. [검증 구조](#5-검증-구조)
6. [실행 환경과 사용 방법](#6-실행-환경과-사용-방법)
7. [확인된 주의점](#7-확인된-주의점)
8. [결론](#8-결론)

## 1. 분석 범위와 요약

이 폴더는 Intel RealSense D435i의 컬러 영상 또는 일반 웹캠 영상에서 파란색 픽셀 영역을 검출하고, 후보 영역에 초록색 사각형을 그리는 OpenCV 학습 예제 모음이다. 핵심 실행 예제 외에 카메라 연결, 영상 색 채널, HSV 조정, 윤곽선 필터링, 미검출 처리, 결과 저장, 좌표 변환을 따로 확인하는 11개 단계별 실험이 포함되어 있다.

설계상 주 흐름은 다음과 같다.

```text
입력 선택(D435i / 웹캠 / 저장 영상 / 합성 영상)
  → 컬러 프레임을 BGR 배열로 획득
  → BGR에서 HSV로 변환
  → 파란색 범위로 이진 마스크 생성
  → 형태학적 잡음 정리
  → 윤곽선 및 면적 기준으로 후보 선택
  → 박스·라벨을 그려 표시하거나 증거 파일로 저장
```

단계별 예제는 하나의 애플리케이션 파이프라인으로 연결되어 자동 실행되는 구조가 아니다. 각 파일을 독립 실행하여 해당 개념을 확인하는 교육용 구성이다.

## 2. 프로젝트 구성

| 파일/폴더 | 역할 |
|---|---|
| [`README.md`](./README.md) | 기준 예제의 설치, 실행, 영상 처리 순서 및 조정 값을 설명한다. |
| [`blue_cube_reference.py`](./blue_cube_reference.py) | README가 기준으로 안내하는 실행 파일. D435i 또는 `--webcam` 입력을 받아 파란 영역을 검출하고 두 창에 표시한다. |
| [`blue_cube.py`](./blue_cube.py) | 별도의 편집 대상 구현. 기준 파일과 HSV 상수가 다르다. |
| [`verify_blue_cube_reference.py`](./verify_blue_cube_reference.py) | 합성 프레임으로 기준 구현의 검출, 색상 제외, 잡음 제거, 빈 화면 및 박스 색을 단언한다. 실행 시 합성 PNG를 폴더에 쓴다. |
| [`test_blue_cube.py`](./test_blue_cube.py) | `blue_cube.detect_blue`를 합성 입력으로 검사하고 PNG 결과를 생성하는 스크립트다. |
| [`step_tests/README.md`](./step_tests/README.md) | 단계별 예제의 환경 설정, 실행 방법, 결과 해석 및 제한 사항을 안내한다. |
| [`step_tests/common.py`](./step_tests/common.py) | 단계별 예제의 공통 입력 인자, 합성 장면, 카메라/이미지 입력, HSV 마스크, 저장 및 표시 함수를 제공한다. |
| [`step_tests/01_d435i_connection.py`–`11_three_scenes.py`](./step_tests/) | 카메라에서 검출 결과 분석에 이르는 개념을 작은 독립 실험으로 나눈다. |
| [`step_tests/verify_examples.py`](./step_tests/verify_examples.py) | 실제 장치 없이 03~11번 예제를 별도 프로세스로 실행하고 주요 합성 경로와 결과 파일을 검사한다. 01·02번의 물리 장치 검사는 포함하지 않는다. |

### 공통 모듈의 역할

`step_tests/common.py`는 `--camera`, `--image`, `--no-gui`, `--out` 인자를 공통으로 정의한다. 입력이 지정되지 않으면 기본 합성 영상을 사용한다. 카메라 입력은 D435i 컬러 스트림 640×480, BGR8, 30 FPS 요청으로 시작하며, 프레임 읽기 함수가 BGR 배열과 호스트 수신 시각을 반환한다. `blue_mask()`는 HSV 범위 지정과 5×5 커널의 열기·닫기를 수행하고, `show()`/`save()`가 결과 이미지 파일 출력과 선택적 GUI 표시를 담당한다.

## 3. 대표 실행 플로우

기준 예제인 [`blue_cube_reference.py`](./blue_cube_reference.py)는 다음 순서로 동작한다.

1. **입력 경로 선택**
   - `--webcam 번호`가 있으면 OpenCV `VideoCapture`를 사용한다.
   - 옵션이 없으면 `pyrealsense2`를 지연 import하고 D435i의 컬러 스트림을 시작한다.
2. **프레임 수집**
   - 카메라는 매 반복마다 새 컬러 프레임을 기다린다.
   - 웹캠은 `cap.read()`로 프레임을 읽는다. 프레임이 없으면 오류를 발생시킨다.
3. **색상 분할**
   - `detect_blue()`가 BGR 프레임을 OpenCV HSV로 바꾼다.
   - H 95~130, S 80 이상, V 50 이상인 픽셀을 마스크에 남긴다.
4. **마스크 후처리 및 후보 생성**
   - 5×5 커널로 morphology open을 적용해 작은 점을 제거하고 close를 적용해 작은 구멍을 메운다.
   - 외부 윤곽선을 찾아 면적 500 이상인 윤곽선의 bounding box를 만든다.
5. **표시**
   - 원본 복사본에 초록색 사각형과 `BLUE` 라벨을 그린다.
   - 검출 화면과 이진 마스크를 별도 OpenCV 창에 표시한다.
   - `q` 또는 Esc 입력으로 반복을 끝낸다.
6. **자원 정리**
   - `finally`에서 시작한 RealSense pipeline 또는 웹캠을 해제하고 OpenCV 창을 닫는다.

실행 명령은 프로젝트 README에 안내된 대로 기준 파일을 직접 호출하거나, 일반 웹캠 사용 시 `--webcam 0`처럼 장치 번호를 지정한다. 기본 실행에는 GUI 표시가 필요하며 일반 SSH 터미널에서는 창이 보이지 않는다.

## 4. 단계별 실험 플로우

| 순서 | 예제 | 확인하는 내용과 앞뒤 관계 |
|---:|---|---|
| 01 | [`01_d435i_connection.py`](./step_tests/01_d435i_connection.py) | D435i 연결, 장치 정보, 컬러 프레임의 shape·dtype·BGR8 확인. 실제 카메라가 필요하다. |
| 02 | [`02_usb_profiles.py`](./step_tests/02_usb_profiles.py) | 장치가 노출하는 컬러 프로파일과 USB 연결 정보를 조사한다. 프로파일 목록은 실측 FPS 보장이 아니다. |
| 03 | [`03_encoding_dtype_shape.py`](./step_tests/03_encoding_dtype_shape.py) | 입력 배열 형식과 색 인코딩을 구별한다. 기본 입력 외에 저장 이미지 및 ROS Image 수신 경로를 제공한다. |
| 04 | [`04_rgb_bgr_mistake.py`](./step_tests/04_rgb_bgr_mistake.py) | 같은 픽셀도 RGB/BGR 해석이 바뀌면 HSV 색조와 마스크가 달라지는 것을 비교한다. |
| 05 | [`05_hsv_tuning.py`](./step_tests/05_hsv_tuning.py) | H/S/V 경계를 트랙바로 조정해 실제 조명과 대상 색에 맞춘다. |
| 06 | [`06_candidate_selection.py`](./step_tests/06_candidate_selection.py) | 최소 면적, ROI 및 가로세로 비율로 후보를 거르고 가장 큰 후보를 선택한다. 색 검출을 후보 선택으로 좁히는 단계다. |
| 07 | [`07_moments_zero.py`](./step_tests/07_moments_zero.py) | 윤곽선 면적 모멘트 `m00`이 0이면 중심을 계산할 수 없음을 확인한다. |
| 08 | [`08_target_loss.py`](./step_tests/08_target_loss.py) | 검출→소실→재검출 상황에서 미검출의 중심을 `None`으로 표현하고, 이전 중심 재사용 오류를 보여준다. |
| 09 | [`09_save_evidence.py`](./step_tests/09_save_evidence.py) | 원본·마스크·오버레이·JSON을 같은 샘플 ID로 저장한다. 거리값은 컬러 입력만으로 얻지 않으므로 `None`이다. |
| 10 | [`10_resize_crop_coordinates.py`](./step_tests/10_resize_crop_coordinates.py) | crop 오프셋과 실제 x/y 축소 비율을 사용해 축소 영상 좌표를 원본 좌표로 복원한다. |
| 11 | [`11_three_scenes.py`](./step_tests/11_three_scenes.py) | 명확한 대상·빈 배경·부분 가림을 비교하고 TP/TN/FP/FN 유형을 기록한다. 세 장면은 기능 확인용이지 정확도 평가 데이터셋은 아니다. |

큰 흐름으로 보면 **장치·데이터 확인(01~03) → 색 해석과 임계값 설정(04~05) → 후보 선택과 기하 처리(06~08) → 결과 기록과 좌표·장면 검증(09~11)** 순서다. 다만 단계 번호는 학습 순서를 안내할 뿐, 각 스크립트가 이전 파일의 결과를 입력으로 받는다는 의미는 아니다.

## 5. 검증 구조

- [`verify_blue_cube_reference.py`](./verify_blue_cube_reference.py)는 합성 파란 사각형을 기준 구현에 넣고 예상 bounding box, 초록색 박스 픽셀, 빈 영상의 미검출 등을 `assert`로 검사한다.
- [`test_blue_cube.py`](./test_blue_cube.py)는 비슷한 합성 사례를 `blue_cube.py` 대상으로 실행한다.
- [`step_tests/verify_examples.py`](./step_tests/verify_examples.py)는 RGB/BGR 변환, 미지원 encoding 거부, 면적 0 중심 처리, 빈 장면 및 부분 가림 검출, 후보 선택 등을 직접 확인한 뒤 예제 파일을 임시 출력 폴더에서 subprocess로 실행한다.
- 단계별 검증은 실제 D435i, ROS 연결, GUI 및 실제 조명/배경에서의 품질을 증명하지 않는다.
- 이 분석에서는 검증 스크립트를 실행하지 않았다. 특히 상위 폴더의 기준 검증 스크립트는 `blue_cube_synthetic.png` 및 `blue_mask_synthetic.png`를 현재 폴더에 쓸 수 있기 때문이다.

## 6. 실행 환경과 사용 방법

README들은 Python 가상환경에 NumPy와 GUI 지원 `opencv-python`을 설치하는 방법을 안내한다. D435i 경로에는 `pyrealsense2`와 시스템의 RealSense SDK/장치 권한 구성이 추가로 필요하다. GUI 패키지와 `opencv-python-headless`를 동시에 설치하지 않도록 안내하고 있다.

단계별 예제 대부분은 기본 합성 영상, `--image`로 지정한 저장 이미지, 또는 `--camera` D435i 입력을 선택한다. 창이 없는 환경에서는 `--no-gui --out 경로`로 이미지 파일을 저장할 수 있다. 03번의 `--ros`는 SDK pipeline을 켜는 대신 이미 실행 중인 ROS 카메라 노드의 이미지 토픽을 구독하는 별도 경로다.

## 7. 확인된 주의점

1. **기준 파일과 편집 파일의 색상 범위가 다르다.** [`blue_cube_reference.py`](./blue_cube_reference.py)는 파란색에 해당하는 H=95~130 범위를 사용한다. 반면 [`blue_cube.py`](./blue_cube.py)는 변수명이 `LOWER_BLUE`/`UPPER_BLUE`인데 H=15~35를 지정한다. OpenCV HSV에서 이 범위는 일반적인 파란색 범위가 아니다.
2. **`test_blue_cube.py` 기대값과 `blue_cube.py`의 범위가 맞지 않는다.** 테스트의 합성 대상은 BGR 파란색 `(255,0,0)`인데, 테스트가 import하는 구현은 H=15~35를 필터링한다. 따라서 합성 파란 사각형이 검출되지 않아 assertion이 실패할 것으로 예상된다. 이는 코드를 실행한 결과가 아니라 두 파일의 조건과 테스트 입력을 대조한 정적 분석이다.
3. **검출은 색 기반 후보 검출이다.** 파란 배경·옷·책 등 같은 색 물체도 후보가 될 수 있다. 3D 큐브 인식, 깊이/거리 추정, 자세 추정 또는 모터 제어는 포함하지 않는다.
4. **카메라 검증과 합성 검증은 별개다.** 합성 영상 성공은 USB 연결, 장치 점유, ROS QoS, GUI, 실제 조명에서의 HSV 범위를 보장하지 않는다.
5. **파일 실행은 결과물을 생성할 수 있다.** 상위 폴더 검증 스크립트는 PNG를 덮어쓸 수 있고, 개별 예제도 기본적으로 `results` 아래에 이미지를 기록한다. 프로젝트 내부 파일 보존이 필요한 경우 실행 전 출력 경로 및 스크립트 동작을 확인해야 한다.

## 8. 결론

이 예제 모음의 교육 흐름은 카메라 입력과 픽셀 표현을 이해한 뒤, HSV 색 분할과 윤곽선 필터링으로 파란 영역 후보를 만들고, 미검출·좌표 변환·결과 저장을 다루는 방식이다. 기준 실행 경로는 [`blue_cube_reference.py`](./blue_cube_reference.py)이고 단계별 세부 학습은 [`step_tests/README.md`](./step_tests/README.md)에서 안내한다. 향후 실제 실행 전에 어떤 구현을 기준으로 사용할지 정하고, 특히 `blue_cube.py`의 HSV 값과 이를 대상으로 하는 테스트 간 불일치를 해소해야 한다.
