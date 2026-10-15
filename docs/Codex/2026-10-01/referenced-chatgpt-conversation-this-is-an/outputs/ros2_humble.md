# ROS 2 Humble 환경 점검 및 실습 가이드

## 목차

1. [개요](#개요)
2. [기본 명령](#기본-명령)
3. [워크스페이스와 빌드](#워크스페이스와-빌드)
4. [환경 점검 1~10](#환경-점검-110)
5. [실습 및 트러블슈팅](#실습-및-트러블슈팅)
6. [최종 체크리스트](#최종-체크리스트)

## 개요

Ubuntu 22.04에서 ROS 2 Humble이 정상적으로 설치되고, 패키지와 노드 간 통신이 동작하는지 확인하는 문서입니다. 원본의 환경 점검 매뉴얼 1~10과 ROS2 실습 기록을 함께 정리했습니다.

## 기본 명령

| 작업 | 명령 |
|---|---|
| 배포판 확인 | `echo $ROS_DISTRO` |
| CLI 도움말 | `ros2 --help` |
| 패키지 일부 확인 | `ros2 pkg list \| head` |
| 전체 패키지 확인 | `ros2 pkg list` |
| Doctor 기본 검사 | `ros2 doctor` |
| Doctor 상세 보고서 | `ros2 doctor --report` |
| 워크스페이스 빌드 | `colcon build` |
| 워크스페이스 환경 적용 | `source install/setup.bash` |

## 워크스페이스와 빌드

### ROS2_WS 구조

원본 실습 워크스페이스 경로는 `~/Sparta/workspace/ROS2_WS`입니다.

| 패키지 | 언어/구성 | 주요 역할 |
|---|---|---|
| `demo_py_pkg` | Python, `talker.py` | `std_msgs/String` 메시지를 상대 토픽 `chatter`로 발행하는 Publisher. `publish_period`, `message_prefix` 파라미터를 사용합니다. |
| `demo_cpp_pkg` | C++, `listener.cpp` | 상대 토픽 `chatter`를 구독해 로그를 출력하는 Subscriber. `log_prefix` 파라미터를 사용합니다. |
| `demo_bringup` | Launch/YAML, `demo.launch.py`, `params.yaml` | Python·C++ 노드를 함께 실행하고 환경을 동적으로 제어합니다. |

### 구현 기록과 모범 사례

1. 소스 코드에서 상대 토픽명 `chatter`를 사용하고, launch 파일의 `remappings`로 실행 시 이름을 바꿉니다.
2. `PushRosNamespace('demo')`를 사용해 노드를 `demo` 네임스페이스로 묶습니다.
3. YAML의 `/**` 와일드카드로 네임스페이스가 달라져도 파라미터가 적용되도록 하고, `ParameterValue`로 타입을 지정합니다.
4. `IfCondition`과 `use_listener:=false` 옵션으로 특정 노드 실행을 제어합니다.

### 빌드 및 실행

```bash
cd ~/Sparta/workspace/ROS2_WS
colcon build
source install/setup.bash
ros2 launch demo_bringup demo.launch.py
```

## 환경 점검 1~10

### 1. ROS 2 배포판 확인

```bash
echo $ROS_DISTRO
```

정상 결과는 `humble`입니다. 아무것도 출력되지 않으면 현재 터미널에 ROS 2 환경 설정이 적용되지 않았을 수 있습니다.

### 2. ROS 2 CLI 확인

```bash
ros2 --help
```

도움말과 `action`, `bag`, `component`, `daemon`, `launch`, `node`, `param`, `pkg`, `run`, `topic` 등 하위 명령 목록이 출력되면 정상입니다.

### 3. ROS 2 패키지 인식 확인

```bash
ros2 pkg list | head
```

전체 목록은 `ros2 pkg list`로 확인합니다. 예시 패키지로 `ackermann_msgs`, `action_msgs`, `action_tutorials_cpp`, `action_tutorials_interfaces`, `action_tutorials_py`, `actionlib_msgs`, `ament_cmake`, `ament_cmake_auto`, `ament_cmake_copyright`, `ament_cmake_core` 등이 있습니다.

`ros2 pkg list | head` 실행 끝에 다음이 표시될 수 있습니다.

```text
BrokenPipeError: [Errno 32] Broken pipe
```

`head`가 앞부분만 읽고 종료한 뒤 ROS 2가 계속 출력하려고 해서 생기는 메시지입니다. 이 현상만으로 ROS 2 설치 오류라고 판단하지 않습니다.

### 4. ROS 2 Doctor 기본 검사

```bash
ros2 doctor
```

원본 기준 정상 결과는 `All 5 checks passed`입니다.

### 5. ROS 2 Doctor 상세 검사

```bash
ros2 doctor --report
```

다음 항목을 확인합니다.

- **Platform Information:** 예를 들어 `system: Linux`, `platform info: Linux-6.8.0-...-x86_64-with-glibc2.35`, `processor: x86_64`가 표시됩니다.
- **RMW Middleware:** 현재 사용하는 DDS/RMW 구현을 표시합니다. 원본 기준 예시는 `rmw_fastrtps_cpp`입니다.
- **ROS 2 Information:** Humble 기준 `distribution name: humble`, `distribution type: ros2`, `distribution status: active`, `release platforms: {'rhel': ['8'], 'ubuntu': ['jammy']}`를 확인합니다. 특히 배포판 이름과 active 상태를 봅니다.
- **Topic List:** ROS 2 노드가 실행 중이지 않을 때 `topic: none`, publisher와 subscriber count가 모두 0일 수 있습니다. 이는 실행 중인 노드가 없다는 뜻이며 설치 오류가 아닙니다.

### 6. 주요 패키지 설치 확인

`ros2 doctor --report`의 PACKAGE VERSIONS 항목을 확인합니다.

- **Navigation:** `navigation2`, `nav2_bringup`, `nav2_amcl`, `nav2_controller`, `nav2_planner`, `nav2_map_server`
- **SLAM:** `slam_toolbox`, `cartographer_ros`
- **Gazebo:** `gazebo_ros`, `gazebo_ros2_control`, `gazebo_plugins`, `gazebo_ros_pkgs`
- **RViz:** `rviz2`, `rviz_common`, `rviz_default_plugins`
- **ros2_control:** `ros2_control`, `controller_manager`, `diff_drive_controller`, `joint_state_broadcaster`
- **Python / C++:** `rclpy`, `rclcpp`
- **TF / Robot Description:** `tf2`, `tf2_ros`, `robot_state_publisher`, `urdf`, `xacro`
- **TurtleBot3:** `turtlebot3`, `turtlebot3_bringup`, `turtlebot3_gazebo`, `turtlebot3_navigation2`, `turtlebot3_description`

### 7. 패키지 업데이트 경고 판단

다음과 같은 `UserWarning`은 보통 설치 실패가 아니라 더 새 버전이 있다는 알림입니다.

```text
UserWarning: ... has been updated to a new version.
local: ... < latest: ...
```

원본 예시는 `imu_sensor_broadcaster`가 `2.53.3 < 2.54.0`, `diff_drive_controller`가 `2.53.3 < 2.54.0`인 경우입니다. 점검만을 위해 모든 패키지를 최신으로 올릴 필요는 없습니다. ROS 2, Gazebo, ros2_control 사이의 버전 호환성을 고려하고, 정상 동작 중인 환경은 무작정 전체 업데이트하지 않습니다.

### 8. 실제 ROS 2 통신 테스트

터미널 1에서 Publisher를 실행합니다.

```bash
ros2 run demo_nodes_cpp talker
```

`Publishing: 'Hello World: 0'`처럼 메시지가 증가하면 정상입니다. 다른 터미널에서 토픽을 확인하고 구독합니다.

```bash
ros2 topic list
ros2 topic echo /chatter
```

`/chatter`가 보이고 메시지가 반복 출력되면 Publisher와 Subscriber 간 Topic 통신이 동작합니다.

### 9. 최종 점검 항목

다음 체크리스트를 모두 확인합니다.

- `echo $ROS_DISTRO` → `humble`
- `ros2 --help` → CLI 정상
- `ros2 pkg list` → 패키지 인식
- `ros2 doctor` → `All 5 checks passed`
- `ros2 doctor --report` → Humble, active, RMW 확인
- Nav2, Gazebo, RViz2, ros2_control, SLAM, TurtleBot3 주요 패키지 확인
- `demo_nodes_cpp talker` 실행
- `ros2 topic list`에서 `/chatter` 확인
- `ros2 topic echo /chatter`로 통신 확인

### 10. 현재 PC에서 확인된 기준 상태

원본 매뉴얼에 기록된 실제 확인 결과입니다.

- ROS 2 distribution: **Humble**
- distribution status: **active**
- RMW: **rmw_fastrtps_cpp**
- ROS 2 Doctor: **5/5 checks passed**
- OS 계열: **Ubuntu 22.04 (Jammy)**
- CPU architecture: **x86_64**
- Nav2, Gazebo, RViz2, ros2_control, SLAM 관련 패키지, TurtleBot3 관련 패키지 설치 확인
- `rclpy` / `rclcpp` 설치 확인

이 기록의 핵심 판단은 ROS 2 Humble 설치, CLI, 패키지 인식, Doctor 점검이 정상이며, 실제 노드/토픽 통신 테스트를 통해 동작을 최종 검증한다는 것입니다.

## 실습 및 트러블슈팅

### `Package 'demo_bringup' not found`

현재 터미널의 `AMENT_PREFIX_PATH`에 해당 워크스페이스가 등록되지 않았을 수 있습니다. 빌드 후 환경을 적용합니다.

```bash
cd ~/Sparta/workspace/ROS2_WS
colcon build
source install/setup.bash
ros2 launch demo_bringup demo.launch.py
```

빌드한 터미널마다 필요한 setup 파일을 source해야 합니다.

### VS Code 진단 표시 설정 기록

원본에 기록된 오류 표시 설정 방법입니다. 실제 오류 원인을 고치는 대신 진단 표시를 숨기면 문제가 가려질 수 있으므로 필요한 경우에만 적용합니다.

- **Python (Pylance):** 해당 줄 뒤에 `# type: ignore` 추가
- **C / C++ (IntelliSense):** `.vscode/settings.json`에 다음 설정 추가
  ```json
  { "C_Cpp.errorSquiggles": "disabled" }
  ```
- **TypeScript / JavaScript:** 코드 상단에 `// @ts-ignore` 추가

### Antigravity CLI 기록

- 기본 실행: `agy`
- 도움말: `agy --help`
- 종료: `/exit` 또는 `Ctrl + D` (원본에는 두 번이라고 기록됨)

## 최종 체크리스트

- [ ] `echo $ROS_DISTRO`가 `humble`인지 확인했다.
- [ ] `ros2 --help`, `ros2 pkg list`, `ros2 doctor`가 정상인지 확인했다.
- [ ] Doctor 보고서에서 Humble active 상태와 RMW를 확인했다.
- [ ] 필요 패키지를 확인하고 버전 경고를 오류와 구분했다.
- [ ] 워크스페이스를 빌드한 뒤 `source install/setup.bash`를 실행했다.
- [ ] `demo_bringup` 실행 및 `/chatter` 통신을 확인했다.
- [ ] `build/`, `install/`, `log/`가 Git에 포함되지 않도록 확인했다.
