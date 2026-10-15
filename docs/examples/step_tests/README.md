# OpenCV·D435i 개념별 확인 — 독립 실행 파이썬 예제

11개 예제를 하나씩 실행하며 강의의 설명을 확인한다. 모든 파일에 파이썬 문법과 OpenCV 함수의 입력·출력·사용 이유를 주석으로 적었다. 공통 입출력은 `common.py`에 있으므로 **이 폴더 전체를 함께 복사**한다. 기존 `blue_cube.py`는 수정하지 않는다.

실행 기준은 **D435i를 연결한 Ubuntu 24.04 PC**다. GPU·CUDA·ROS는 기본 예제에 필요하지 않다. RealSense의 파이썬 패키지 이름은 **`pyrealsense2`**다. `pyrealsense`라는 다른 패키지와 혼동하지 않는다.

## 1. venv 생성과 설치

예제 폴더 전체를 `~/opencv-step-tests`에 두었다고 가정한다. 다른 위치에 두었다면 첫 줄을 실제 위치로 바꾼다. 아래 명령은 PC의 터미널에서 실행한다.

```bash
cd ~/opencv-step-tests

# Ubuntu 패키지 관리자로 venv 생성 기능과 영상 표시용 라이브러리를 준비한다.
sudo apt update
sudo apt install -y python3-venv python3-pip libgl1 libglib2.0-0t64

# 현재 PC의 Python으로 이 예제 전용 가상환경을 만든다.
python3 -m venv .venv

# 이후 python과 pip가 .venv를 사용하도록 활성화한다.
source .venv/bin/activate

# pip 자체를 갱신한 뒤 필요한 패키지를 설치한다.
python -m pip install --upgrade pip
python -m pip install numpy opencv-python
python -m pip install pyrealsense2

# 설치 위치와 의존성 상태를 확인한다.
which python
python --version
python -m pip check
python -c "import sys, cv2, numpy, pyrealsense2; print(sys.executable); print('OpenCV:', cv2.__version__); print('NumPy:', numpy.__version__); print('RealSense import OK')"
```

`which python`의 경로가 예제 폴더의 `.venv/bin/python`으로 끝나야 한다. `python -m pip`를 사용하면 실행할 Python과 패키지를 설치할 Python이 일치한다. **`sudo pip`나 `--break-system-packages`는 사용하지 않는다.**

`opencv-python`의 파이썬 import 이름은 `cv2`다. GUI 창을 사용하는 예제이므로 `opencv-python-headless`와 함께 설치하지 않는다. RealSense가 없는 PC는 `pyrealsense2` 설치를 생략해도 합성 영상 예제를 실행할 수 있다. 카메라 예제에는 반드시 필요하다.

수업에서 동작을 확인한 환경은 버전을 기록한다.

```bash
python -m pip freeze > requirements-tested.txt
```

새 터미널을 열 때는 **설치를 반복하지 않고 활성화만** 한다.

```bash
cd ~/opencv-step-tests
source .venv/bin/activate
```

종료할 때는 `deactivate`를 입력한다.

## 2. 카메라 사용 전 확인

1. D435i를 PC의 USB 3 포트에 데이터 전송이 가능한 케이블로 직접 연결한다.
2. RealSense Viewer와 ROS 카메라 노드를 종료한다. SDK 수집과 ROS wrapper 수집을 동시에 시작하지 않는다.
3. SDK·장치 권한(udev) 설정은 기존 [D435i 설치·관측 가이드](../../../모듈2_3_D435i_설치와_관측가이드.md)를 따른다. pip 설치는 Python 바인딩 준비이며 Linux 장치 권한 설정을 모두 대신하지 않는다.
4. 첫 확인은 다음 두 파일로 한다.

```bash
python 01_d435i_connection.py
python 02_usb_profiles.py
```

연결 확인이 실패했다고 무조건 점유 충돌이라고 판단하지 않는다. 케이블·포트·권한·장치 점유·요청 프로파일을 확인한다. 여러 대가 연결되면 `01_d435i_connection.py --serial 실제시리얼번호`로 선택한다.

## 3. 예제와 확인할 결과

| 번호 | 파일 | 카메라 | 확인할 개념·기대 결과 |
|---|---|---|---|
| 01 | `01_d435i_connection.py` | 필수 | 장치 이름·시리얼·USB 정보를 출력하고 컬러 배열 `480×640×3`, `uint8`, `bgr8`을 확인한다. |
| 02 | `02_usb_profiles.py` | 필수 | USB 연결 정보와 장치가 노출하는 해상도·FPS·형식 목록을 출력한다. USB 2/3 연결에서 각각 비교한다. |
| 03 | `03_encoding_dtype_shape.py` | 선택 | encoding·dtype·shape를 출력한다. RGB 저장용 `.npy` 배열도 생성한다. `--ros` 경로에서는 실제 ROS Image를 읽는다. |
| 04 | `04_rgb_bgr_mistake.py` | 선택 | 동일한 파란 BGR 픽셀을 제대로 해석하면 H=120, RGB로 오해하면 H=0이 된다. 두 마스크가 달라진다. |
| 05 | `05_hsv_tuning.py` | 선택 | 6개 트랙바로 H/S/V 하한·상한을 조절한다. 시작 범위는 H=95~130, S≥80, V≥40이다. |
| 06 | `06_candidate_selection.py` | 선택 | 면적·작업 영역·가로세로 비율로 후보를 거른다. 노란 ROI 안에서 선택한 후보 하나에 초록색 박스를 그린다. |
| 07 | `07_moments_zero.py` | 불필요 | 일직선 윤곽선은 m00=0으로 중심 None, 정상 사각형은 중심 `(20,20)`이다. |
| 08 | `08_target_loss.py` | 불필요 | 검출→소실→재검출에서 `detected=false`, `center=None`을 확인한다. 빨간 표시는 잘못 재사용한 이전 중심이다. |
| 09 | `09_save_evidence.py` | 선택 | 같은 ID로 원본·mask·overlay·JSON을 저장한다. 시간·검출 여부·중심·정규화 오차·해상도를 기록한다. |
| 10 | `10_resize_crop_coordinates.py` | 선택 | crop 오프셋과 실제 축소 배율로 원본 좌표를 복원한다. 초록 표시는 복원 좌표, 빨간 표시는 잘못 재사용한 축소 좌표다. |
| 11 | `11_three_scenes.py` | 선택 | 명확한 물체·빈 배경·부분 가림을 비교하고 TP/FP/FN/TN을 기록한다. |

기본 입력은 합성 영상이다. 카메라가 선택 사항인 파일에 `--camera`를 붙이면 D435i 입력을 사용한다. 07·08은 합성 상태 실험이므로 카메라 옵션을 사용하지 않는다. 01·02는 자동 검사 시 장치 없이 실행하지 않는다.

## 4. 한 파일씩 실행하기

```bash
# 합성 영상: 창과 results 폴더의 저장 파일을 함께 확인한다.
python 03_encoding_dtype_shape.py
python 04_rgb_bgr_mistake.py
python 05_hsv_tuning.py
python 06_candidate_selection.py
python 07_moments_zero.py
python 08_target_loss.py
python 09_save_evidence.py
python 10_resize_crop_coordinates.py
python 11_three_scenes.py
```

대부분의 정지 영상 창은 창을 선택한 뒤 아무 키나 누르면 닫힌다. 05번은 트랙바 조정 후 **q 또는 Esc**로 종료하며 최종 HSV 범위를 터미널에 출력한다.

```bash
# 실제 장면을 보며 HSV 조정
python 05_hsv_tuning.py --camera

# 실제 카메라 한 장에서 후보 선택
python 06_candidate_selection.py --camera

# 실제 샘플 증거 저장: 창 없이 파일로 저장한다.
python 09_save_evidence.py --camera --out results/camera_sample

# 세 장면을 순서대로 준비하고 터미널에서 Enter
python 11_three_scenes.py --camera --out results/three_scenes

# 저장한 사진으로 채널 순서 오류 비교
python 04_rgb_bgr_mistake.py --image my_frame.png
```

11번의 부분 가림은 물체 일부가 보이는 장면이다. 기대값은 검출이지만 형태·면적 조건에 따라 미검출될 수 있다. 세 장면의 결과만으로 일반적인 검출 정확도를 주장하지 않는다.

## 5. SSH 또는 창 없는 환경

일반 SSH 터미널에서는 `imshow` 창을 표시할 수 없다. PC의 데스크톱 터미널에서 GUI 예제를 실행하거나, `--no-gui`로 파일만 저장한 뒤 이미지를 열어 확인한다.

```bash
python 04_rgb_bgr_mistake.py --no-gui --out results/channel_order
python 05_hsv_tuning.py --no-gui --out results/hsv_initial
python 06_candidate_selection.py --camera --no-gui --out results/candidate
```

05번의 `--no-gui`는 트랙바를 제공하지 않고 시작 HSV 범위의 결과 한 장을 저장한다. SSH만 사용할 때는 파일 상단 `initial` 값을 바꾸고 결과를 비교한다. 이 자료의 카메라 연결 대상은 PC이며 Pi의 OpenCR 업로드·제어 환경과 분리한다.

## 6. ROS Image 확인은 별도 경로다

03번의 `--ros`는 SDK를 켜지 않고 **이미 실행 중인 ROS 카메라 노드의 메시지를 구독**한다. 기존 설치 가이드에서 구성한 PC의 NVIDIA Isaac ROS/Lyrical 환경을 사용한다. 이 예제를 위해 Ubuntu 24.04에 다른 배포판용 ROS 패키지를 섞어 설치하지 않는다.

일반 venv에는 `rclpy`, `cv_bridge`, `sensor_msgs`가 보이지 않을 수 있다. **ROS를 설치한 Python 환경**에서 실행한다. 가상환경 안이었다면 먼저 `deactivate`한다.

```bash
# 기존 ROS 설치 경로가 다르면 실제 setup.bash 경로를 사용한다.
source /opt/ros/lyrical/setup.bash

# 실제 카메라 토픽 이름을 확인한다.
ros2 topic list

# 토픽 이름은 ros2 topic list에서 확인한 값으로 바꾼다.
python3 03_encoding_dtype_shape.py --ros --topic /camera/camera/color/image_raw
```

ROS 작업 환경에 필요한 모듈이 있는지 먼저 확인한다.

```bash
python3 -c "import rclpy, cv_bridge, sensor_msgs, cv2, numpy; print('ROS Python import OK')"
```

`--ros`와 `--camera`는 함께 사용하지 않는다. SDK 수집을 끝낸 뒤 ROS 노드를 켜거나 그 반대로 전환한다. ROS 이미지의 `header.stamp`, SDK 프레임 타임스탬프, 호스트 `monotonic_ns`는 같은 시계가 아니다.

## 7. 결과를 읽는 기준

- **픽셀과 배열:** 화면 좌표는 `(x,y)`, NumPy 접근은 `[y,x]`다. 영상 shape는 `(높이,너비,채널)`이다.
- **색:** 일반 uint8 OpenCV HSV는 H=0~179, S/V=0~255다. float HSV 또는 HSV_FULL과 혼동하지 않는다.
- **검출:** 색으로 후보를 찾는 방식이다. 파란 물체의 3D 큐브 형태를 판별하지 않는다.
- **중심:** m00=0은 나누지 않는다. 미검출 시 중심은 None이며 이전 값을 새 결과처럼 쓰지 않는다.
- **거리:** 컬러 영상만 사용하므로 `distance_m=None`이다. 임의의 거리 숫자를 채우지 않는다.
- **정규화 오차:** 09번은 `ex=(cx-(W-1)/2)/(W/2)`를 사용한다. 무차원이고 오른쪽이 양수다.
- **좌표 복원:** 10번은 픽셀 중심 규약으로 `x=(u+0.5)/sx-0.5+x0`를 사용한다. crop 오프셋과 축별 실제 배율을 함께 적용한다.
- **시간:** 09번은 호스트 수신 monotonic 시각[ns]를 기록한다. 절대 시각이나 카메라 노출 시각으로 해석하지 않는다.
- **USB/FPS:** 02번은 프로파일 목록 확인이다. 실제 FPS 측정이나 모든 컬러·깊이 조합의 동시 실행 성공을 보장하지 않는다.

## 8. 설치·실행 오류

| 현상 | 확인·조치 |
|---|---|
| `No module named cv2` | `which python`이 `.venv/bin/python`인지 확인하고 그 환경에서 `python -m pip install opencv-python`을 실행한다. |
| `No module named pyrealsense2` | 같은 venv에서 `python -m pip install pyrealsense2`를 실행한다. |
| `No matching distribution found` | `python --version`, `uname -m`, `python -m pip debug --verbose`로 Python·아키텍처를 확인한다. 해당 조합의 wheel이 없으면 기존 RealSense SDK 바인딩 설치 절차를 따른다. Pi의 arm64와 PC의 x86_64는 다르다. |
| `libGL.so.1` 오류 | PC에서 `sudo apt install libgl1`을 확인한다. |
| GUI/Qt/xcb 오류 | 데스크톱 터미널인지, `echo "$DISPLAY"`가 비어 있지 않은지 확인한다. 창이 필요 없으면 `--no-gui`를 사용한다. |
| 장치 없음·권한 오류 | USB 데이터 케이블·포트·udev 설정을 확인한다. Python을 sudo로 실행하는 것을 기본 해결책으로 삼지 않는다. |
| 장치 busy·프레임 timeout | Viewer·ROS 카메라 노드·다른 SDK 프로그램을 종료한 뒤 하나만 실행한다. 연결·프로파일도 함께 확인한다. |
| 파란 큐브가 검출되지 않음 | 05번에서 실제 mask를 보며 H/S/V를 조정하고 06번의 면적·ROI·형태 조건을 확인한다. |
| 다른 파란 물체에도 박스가 생김 | 색 기반 방식의 한계다. 배경을 정리하거나 ROI/후보 조건을 조정한다. |

## 9. 카메라 없는 자동 확인

```bash
python verify_examples.py
```

03~11번의 합성 입력 경로, RGB/BGR 변환, HSV 상한, 면적 0, 검출 소실, 좌표 복원, 증거 파일 이름을 검사한다. 카메라·ROS·GUI·USB 성능 검증은 별도다.

## 공식 참고

- [Python venv](https://docs.python.org/3/library/venv.html)
- [pip와 가상환경](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
- [RealSense Python 바인딩](https://github.com/realsenseai/librealsense/blob/master/wrappers/python/readme.md)
- [pyrealsense2 배포 파일](https://pypi.org/project/pyrealsense2/)
- [OpenCV 색 공간·HSV](https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html)
- [OpenCV 윤곽선 특징](https://docs.opencv.org/4.x/dd/d49/tutorial_py_contour_features.html)
