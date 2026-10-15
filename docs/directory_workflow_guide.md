# Lv2 Module 5 디렉토리 및 담당 업무 가이드

> 프로젝트: `Lv2_EYE4_Assignment`  
> 대상: Lv2 Module 5  
> 하드웨어: RealSense D435 + Pan/Tilt 2축 Dynamixel + OpenCR  
> 목적: 팀원별 작업 영역과 디렉토리 역할을 명확히 하고, ROS 2 Interface와 검증 절차를 일관되게 유지한다.

---

## 1. 프로젝트 전체 구조

```text
lv2_module5/
├── README.md
├── report.md
├── team.md
├── presentation.md
├── ros2_ws/
│   └── src/
│       ├── realsense_tracker/
│       │   ├── package.xml
│       │   ├── setup.py
│       │   ├── setup.cfg
│       │   ├── resource/realsense_tracker
│       │   ├── realsense_tracker/
│       │   │   ├── __init__.py
│       │   │   ├── camera_node.py
│       │   │   ├── perception_node.py
│       │   │   ├── control_node.py
│       │   │   └── opencr_node.py
│       │   ├── launch/tracker.launch.py
│       │   └── config/tracker.yaml
│       └── realsense_tracker_interfaces/
│           ├── CMakeLists.txt
│           ├── package.xml
│           └── msg/
│               ├── Target.msg
│               └── PanTiltCommand.msg
├── firmware/
│   └── opencr/README.md
├── config/
│   ├── robot.yaml
│   ├── camera.yaml
│   └── opencr.yaml
├── results/
│   ├── images/
│   ├── logs/
│   ├── plots/
│   └── metrics.csv
└── recordings/README.md
```

---

# 2. 담당 파트별 기본 원칙

| 영역 | 주요 담당 | 주요 업무 |
|---|---|---|
| `ros2_ws/src/realsense_tracker/realsense_tracker/` | 통합 + 인지 + 제어 | ROS 2 Node |
| `ros2_ws/src/realsense_tracker_interfaces/` | 통합 관리 + 인지/제어 협의 | Custom Message 계약 |
| `ros2_ws/src/realsense_tracker/launch/` | 통합 | 전체 Node 실행 구성 |
| `ros2_ws/src/realsense_tracker/config/` | 통합 | ROS Node Parameter |
| `firmware/opencr/` | 제어 | OpenCR / Dynamixel 펌웨어와 watchdog |
| `config/` | 통합 관리 + 각 담당 협의 | 하드웨어·제어 설정 |
| `results/`, `recordings/` | 검증·문서화 + 전체 | 시험 결과 및 증빙 |
| `report.md`, `presentation.md`, `team.md` | 전체, 검증·문서화 취합 | 결과 및 팀 기록 |

---

# 3. `ros2_ws/`

ROS 2 Node, Launch, Package, Custom Message가 위치하는 개발 Workspace이다. 통합 담당이 전체 구조를 관리하며 다른 담당자는 합의 없이 Workspace 구조를 바꾸지 않는다.

Git에 올리지 않는 빌드 결과물:

```text
ros2_ws/build/
ros2_ws/install/
ros2_ws/log/
```

---

# 4. `ros2_ws/src/realsense_tracker/`

메인 Python ROS 2 패키지로 실행 Node, Launch, ROS Parameter를 관리한다. 통합 담당은 Package 구조, Topic 연결, Launch, Node 간 데이터 흐름과 전체 실행을 관리한다.

## 4.1 `realsense_tracker/camera_node.py`

**담당:** 통합, 인지 담당과 협업.

RealSense D435 RGB/Depth stream을 ROS 2로 제공한다.

```text
/camera/color/image_raw  sensor_msgs/msg/Image
/camera/depth/image_raw  sensor_msgs/msg/Image
```

주요 작업: RealSense 연결, stream 설정, RGB/Depth publisher, camera parameter 관리, 동작 확인.

---

# 5. `realsense_tracker/perception_node.py`

**담당:** 인지.

RGB/Depth 영상에서 파란색 퍽을 탐지하고 Target 계약에 맞춰 `/target`을 발행한다.

```text
RGB / Depth
  → 파란색 퍽 탐지
  → 중심 좌표 / 정규화 오차 / 면적비 / Depth / 검출 여부
  → /target (realsense_tracker_interfaces/msg/Target)
```

주요 작업: RGB 처리, HSV/Contour 기반 탐지, 중심점과 `error_x_norm`/`error_y_norm` 계산, `area_ratio`, `depth_m`, `detected`, Header timestamp/frame_id 생성, 발행 주기 확인.

미검출은 `detected=false`로 표현한다. Message 필드와 의미는 아래 Interface 계약을 따른다.

---

# 6. `realsense_tracker/control_node.py`

**담당:** 제어, 통합과 협업.

`/target` 입력에서 화면 오차를 읽어 Pan/Tilt 2축 속도 명령을 생성한다.

```text
/target
  → detected / timestamp 확인
  → 수평·수직 오차
  → Pan/Tilt P 제어
  → 속도 제한 / 각도 제한
  → 안전 정지 판단
  → /control/pan_tilt_cmd
```

주요 작업:

- `/target` Subscribe 및 `target_timeout` 처리
- `error_x_norm`을 Pan, `error_y_norm`을 Tilt 제어에 사용
- P 제어와 축별 속도·각도 제한
- 미검출 또는 timeout 시 `stop=true`, 두 속도 0 발행
- 유효 Target 3회 연속 수신 후 추적 재개
- `/motor/state`의 실제 축 상태 확인
- `/control/pan_tilt_cmd` Publish

---

# 7. `realsense_tracker/opencr_node.py`

**담당:** 통합 + 제어.

`/control/pan_tilt_cmd`를 Serial Protocol로 OpenCR에 전달하고, 축 상태를 `/motor/state`로 발행한다.

```text
control_node
  → /control/pan_tilt_cmd
  → opencr_node
  → Serial
  → OpenCR → Pan/Tilt Dynamixel
```

주요 작업: Serial 연결, 명령 Subscribe, ROS 단위와 Firmware 단위 변환, Serial Protocol 변환, 상태 수신, `/motor/state` Publish, 오류 처리.

---

# 8. `launch/`

**담당:** 통합.

`tracker.launch.py`가 camera, perception, control, OpenCR Node와 Parameter를 실행 구성한다.

```bash
ros2 launch realsense_tracker tracker.launch.py
```

---

# 9. ROS 2 `config/tracker.yaml`

통합 담당이 관리하고 각 담당자가 값을 제안한다. Pan/Tilt 제어와 안전 파라미터를 사용한다.

```yaml
camera:
  width: ...
  height: ...
  fps: ...

control:
  kp_pan: ...
  kp_tilt: ...
  pan_speed_limit_rad_s: ...
  tilt_speed_limit_rad_s: ...
  pan_angle_min_rad: ...
  pan_angle_max_rad: ...
  tilt_angle_min_rad: ...
  tilt_angle_max_rad: ...
  target_timeout_sec: ...
  recovery_valid_count: 3

opencr:
  port: ...
  baudrate: ...
  command_timeout_sec: ...
```

`target_timeout_sec`는 Control이 새 유효 Target을 기다리는 제한시간, `command_timeout_sec`는 OpenCR Firmware watchdog의 명령 수신 제한시간이다. 실제 구현은 각 Node의 parameter 선언 형식에 맞춰 구성한다.

---

# 10. `firmware/opencr/`

**담당:** 제어.

OpenCR Arduino 펌웨어에서 Pan/Tilt Dynamixel 명령과 상태를 처리한다. ROS 2 Python 코드와 Firmware 코드는 분리한다.

주요 작업: Serial Protocol, Dynamixel 2축 제어, 상태 반환, Firmware 빌드·업로드·하드웨어 확인.

## 안전 정지와 watchdog

설정된 `command_timeout` 동안 새 제어 명령을 받지 못하면 Firmware watchdog이 두 축을 정지한다. ROS 2가 정지 명령을 보낼 수 없는 상황도 Firmware가 처리해야 한다.

---

# 11. ROS 2 Interface 계약

아래 계약은 이 문서와 `팀업무_네비게이터.md`에서 동일하게 유지한다.

| 방향 | Topic | Message Type | Publisher → Subscriber |
|---|---|---|---|
| Camera → Perception | `/camera/color/image_raw` | `sensor_msgs/msg/Image` | `camera_node` → `perception_node` |
| Camera → Perception | `/camera/depth/image_raw` | `sensor_msgs/msg/Image` | `camera_node` → `perception_node` |
| Perception → Control | `/target` | `realsense_tracker_interfaces/msg/Target` | `perception_node` → `control_node` |
| Control → OpenCR | `/control/pan_tilt_cmd` | `realsense_tracker_interfaces/msg/PanTiltCommand` | `control_node` → `opencr_node` |
| OpenCR → Control | `/motor/state` | `sensor_msgs/msg/JointState` | `opencr_node` → `control_node` |

`ros2_ws/src/realsense_tracker_interfaces/msg/Target.msg`:

```text
std_msgs/Header header
bool detected
float32 center_x_px
float32 center_y_px
float32 error_x_norm
float32 error_y_norm
float32 area_ratio
float32 depth_m
```

`header.stamp`는 결과 생성 시각, `header.frame_id`는 카메라 기준 Frame이다. 중심 좌표는 pixel, 오차는 -1.0~+1.0 정규화 값, 면적비는 0.0~1.0, Depth는 m 단위다. `detected=false`이면 제어는 수치 필드를 사용하지 않는다. 오차 부호는 x축 음수가 화면 왼쪽, 양수가 오른쪽이며 y축 음수가 위쪽, 양수가 아래쪽이다.

`ros2_ws/src/realsense_tracker_interfaces/msg/PanTiltCommand.msg`:

```text
std_msgs/Header header
bool stop
float32 pan_velocity_rad_s
float32 tilt_velocity_rad_s
```

`header.stamp`는 명령 생성 시각, 속도 단위는 rad/s다. `stop=true`이면 양 축 속도 모두 0.0이어야 한다.

모터 상태:

```text
/motor/state
sensor_msgs/msg/JointState
name[] = pan_joint, tilt_joint
position[] = rad
velocity[] = rad/s
effort[] = 하드웨어에서 제공하는 경우 사용
```

---

# 12. 프로젝트 `config/`

```text
config/
├── robot.yaml
├── camera.yaml
└── opencr.yaml
```

## `robot.yaml`

바퀴 관련 파라미터 대신 실제 2축 Joint 이름을 설정한다.

```yaml
robot:
  name: EYE4_tracker
  pan_joint_name: pan_joint
  tilt_joint_name: tilt_joint
```

## `camera.yaml`

```yaml
camera:
  width: ...
  height: ...
  fps: ...
```

담당: 인지 + 통합.

## `opencr.yaml`

```yaml
opencr:
  port: /dev/ttyACM0
  baudrate: ...
  pan_motor_id: ...
  tilt_motor_id: ...
  pan_direction: ...
  tilt_direction: ...
  command_timeout_sec: ...
```

담당: 제어 + 통합. 실제 Serial 및 모터 값은 하드웨어 확인 후 기록한다.

---

# 13. `results/`

**담당:** 검증·문서화가 취합하고 전체가 자료를 제공한다.

```text
results/
├── images/
├── logs/
│   ├── ros2/
│   ├── perception/
│   ├── control/
│   ├── opencr/
│   └── verification/
├── plots/
└── metrics.csv
```

- `images/`: 탐지, 정상 추적, 가림·복구, 안전 정지 증빙
- `logs/`: ROS 2, 인지, 제어, OpenCR, 시험 로그
- `plots/`: 수평 오차, 제어 응답, Kp 비교, 복구 시간 및 검출 성능
- `metrics.csv`: 시험별 조건과 측정 지표. 컬럼은 시험 전 합의하고 일관되게 유지한다.

지표: FPS, Detection Rate, Background False Detection, Horizontal RMSE, Recovery Success, Recovery Time.

---

# 14. `recordings/`

**담당:** 검증·문서화 + 전체.

시험 영상과 rosbag 등 원본 기록을 관리한다. 대용량 파일을 저장소에 직접 추가하지 않는 경우 `recordings/README.md`에 저장 위치, 파일명, 크기, 해시, 접근·재생 방법을 기록한다. 필수 시험의 재현 가능한 증빙을 `results/`와 연결한다.

---

# 15. `report.md`

**담당:** 전체 작성, 검증·문서화가 시험 결과와 증빙을 정리하고 팀장이 확인한다.

```text
1. 프로젝트 개요
2. 시스템 및 하드웨어 구성
3. 소프트웨어 / ROS 2 Interface
4. 인지 알고리즘
5. Pan/Tilt 제어 알고리즘
6. OpenCR / Dynamixel
7. 안전 정지
8. 통합 및 검증 시험
9. 성능 결과
10. 문제점, 한계 및 결론
```

---

# 16. `presentation.md`

**담당:** 전체 작성, 검증·문서화 담당이 결과·증빙 흐름을 정리한다.

```text
인지 → RealSense / 퍽 탐지 / Target 생성
제어 → Pan/Tilt P 제어 / 제한 / 안전 정지
통합 → ROS 2 Interface / OpenCR 연결 / Launch
검증 → 정상 추적 / 가림·복구 / 중단 시험 / 지표
```

---

# 17. `team.md`

**담당:** 팀 전체, 팀장이 최종 확인한다. 역할, Issue, 본인 PR, 리뷰, 구현 및 검증 기여를 실제 이력에 맞춰 기록한다.

---

# 18. 작업 영역 충돌 방지 규칙

## 원칙 1. 다른 담당자의 핵심 코드를 임의로 수정하지 않는다.

```text
인지 → perception_node.py
제어 → control_node.py / firmware/opencr/
통합 → camera_node.py / opencr_node.py / Launch / Package / 전체 연결
검증·문서화 → results / recordings / report / presentation / team
```

## 원칙 2. Topic Interface는 임의로 변경하지 않는다.

확정 계약은 `/target` Target, `/control/pan_tilt_cmd` PanTiltCommand, `/motor/state` JointState이며 Joint 이름은 `pan_joint`, `tilt_joint`다. 변경은 인지·제어·통합 협의와 검증 영향 확인 후 양 문서와 코드에 함께 반영한다.

## 원칙 3. 하드웨어 설정은 `config/`에서 관리한다.

포트, 모터 ID, 방향, Joint 이름, 제한값을 코드에 불필요하게 하드코딩하지 않는다.

## 원칙 4. 빌드 결과물은 Git에 올리지 않는다.

`build/`, `install/`, `log/`는 커밋하지 않는다.

## 원칙 5. 실험 결과는 `results/`에 저장한다.

```text
코드 → ros2_ws/       펌웨어 → firmware/
설정 → config/         시험 자료 → results/ 및 recordings/
문서 → *.md
```

---

# 19. Git 작업 영역

각 팀원은 `dev/<이름>` 브랜치에서 작업한다.

```text
main
├── dev/<이름>
└── dev/<다른_팀원>
```

작업 흐름:

```text
dev/<이름>에서 작업
  → 변경 확인 / commit
  → push
  → Pull Request
  → Review / Approve
  → main Merge
```

예시 명령:

```bash
git switch dev/본인이름
git fetch origin
git merge origin/main
git status
git add <파일>
git commit -m "설명"
git push origin dev/본인이름
```

팀의 기본 흐름은 팀 저장소의 `dev/<이름>`에서 PR을 올리는 방식이며 Fork/Remote 백업을 기본 절차로 두지 않는다. 공유 파일은 수정 전에 충돌 가능성을 확인한다.

---

# 20. 전체 시스템에서 각 담당자의 위치

```text
RealSense D435
  → Camera Node [통합]
  → RGB / Depth
  → Perception Node [인지]
  → /target [Target]
  → Control Node [제어]
  → /control/pan_tilt_cmd [PanTiltCommand]
  → OpenCR Node [통합 + 제어]
  → Serial
  → OpenCR [제어]
  → Pan Dynamixel + Tilt Dynamixel
  → 카메라 방향 변경

검증·문서화: Interface, 안전 정지, 시험 결과와 증빙을 전 흐름에서 확인
```

---

# 21. 한눈에 보는 담당 영역

```text
통합: Workspace / Package / Custom Message / Camera Node / OpenCR Node /
      Launch / Config / Topic 연결 / 전체 통합
인지: RGB/Depth / 파란색 퍽 탐지 / 중심·오차·면적비·Depth / /target
제어: Pan/Tilt P 제어 / 속도·각도 제한 / timeout 정지 /
      OpenCR Firmware / Dynamixel / watchdog
검증·문서화: Interface / 정상 30초 / 가림 2초×5 / 중단 시험 /
             Kp 비교 / 지표 / results·recordings / 보고·발표·팀 문서
```

---

# 22. Phase별 담당

| Phase | 주요 작업 | 주 담당 |
|---|---|---|
| Phase 1 | 환경 구축 및 RealSense/OpenCR 연결 확인 | 통합 + 제어 |
| Phase 2 | ROS 2 구조 및 Custom Message 구축 | 통합 |
| Phase 3 | RGB/Depth, 퍽 탐지, `/target` | 인지 + 통합 |
| Phase 4 | 인지 → 제어 Interface 연결 | 인지 + 제어 + 통합 |
| Phase 5 | OpenCR / Pan·Tilt Dynamixel 연결 | 제어 + 통합 |
| Phase 6 | 안전 정지 / timeout / watchdog | 제어 + 통합 + 검증 |
| Phase 7 | 정상·가림·중단·Kp 시험과 지표 계산 | 전체 + 검증 |
| Phase 8 | results 및 보고·발표·팀 문서화 | 검증·문서화 + 전체 |

---

# 23. 검증·문서화 업무

## 23.1 Interface 검증

```bash
ros2 node list
ros2 topic list
ros2 topic type /target
ros2 topic type /control/pan_tilt_cmd
ros2 topic type /motor/state
ros2 topic info /target
ros2 topic info /control/pan_tilt_cmd
ros2 topic info /motor/state
ros2 topic echo /target
ros2 topic echo /control/pan_tilt_cmd
ros2 topic echo /motor/state
```

Topic 이름과 Type, Publisher/Subscriber, 필드 의미·단위, timestamp, `pan_joint`/`tilt_joint`를 확인한다.

## 23.2 안전 정지 검증

```text
detected=false
  → control_node stop=true, 두 속도 0
/target 입력 중단
  → target_timeout → control_node 정지
/control/pan_tilt_cmd 중단
  → command_timeout → OpenCR Firmware watchdog 정지
정지 후 유효 Target 3회 연속 수신
  → 추적 복구
```

## 23.3 필수 시험

- 정상 추적 30초
- 약 2초 가림 × 5회
- `/target` 입력 중단
- `/control/pan_tilt_cmd` 통신 중단
- 최소 2개 `Kp` 설정 비교

## 23.4 성능 지표

- FPS
- Detection Rate
- Background False Detection
- Horizontal RMSE
- Recovery Success
- Recovery Time

원본 로그·영상·CSV와 계산 근거를 `results/`와 `recordings/`에 저장한다. 실패 시험도 제외하지 않는다.

---

# 24. 최종 작업 원칙

```text
camera_node.py → 통합
perception_node.py → 인지
control_node.py → 제어
opencr_node.py → 통합 + 제어
realsense_tracker_interfaces/ → 통합 관리 + 인지/제어 협의
tracker.launch.py / tracker.yaml → 통합
config/*.yaml → 통합 관리 + 각 담당 설정 협의
firmware/opencr/ → 제어
results/ / recordings/ / report.md / presentation.md / team.md
  → 검증·문서화 중심 + 전체 협업
```

개발 흐름:

```text
Interface 계약 확인
  → 인지·제어 구현 및 단독 확인
  → ROS 2 Topic 연결
  → OpenCR 연결
  → 안전 정지 통합
  → 정상/가림/중단/Kp 시험
  → 지표 산출
  → results 및 문서 정리
```

> 각 담당자는 자신의 기능을 구현하고, 통합 담당은 기능을 하나의 ROS 2 시스템으로 연결하며, 검증·문서화 담당은 Interface·안전 정지·시험 결과가 재현되는지 확인한다.
