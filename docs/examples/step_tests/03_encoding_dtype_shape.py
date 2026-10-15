# 이 파일에서 읽어야 할 문법·계산
# conversions는 encoding 문자열을 변환 코드에 연결한 딕셔너리다. conversions[encoding]으로 해당 코드를 꺼낸다.
# received=[]는 수신된 메시지를 모을 리스트다. 콜백 함수는 append로 메시지를 추가한다.
# frame if encoding=="rgb8" else ...는 RGB인 경우 그대로 사용하고 BGR일 때만 채널을 바꾼다.
# hsv[:,:,0]은 모든 y·모든 x에서 첫 채널 H만 선택한다. 결과 shape는 H×W의 2차원이다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""encoding·dtype·shape·RGB 저장 규약. --ros이면 실제 ROS Image 한 장을 확인한다."""
# cv2는 OpenCV의 파이썬 모듈명이다. 설치할 때의 패키지 이름은 opencv-python이다.
import cv2
# NumPy를 np라는 별명으로 불러온다. 영상은 숫자를 담은 다차원 배열이다.
import numpy as np
# 같은 폴더의 common.py에서 이름을 가져온다. 카메라/파일 입출력과 저장을 재사용한다.
from common import parser, read_once, show

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def to_hsv(array, encoding):
    # 세 번째 축은 채널 수다. ndim은 축 개수이며 앞 조건부터 검사하여 2차원 배열에서 잘못된 축 접근을 피한다.
    if array.dtype != np.uint8 or array.ndim != 3 or array.shape[2] != 3:
        # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
        raise ValueError('이 예제는 uint8 H×W×3 컬러 영상만 처리한다.')
    conversions = {'rgb8': cv2.COLOR_RGB2HSV, 'bgr8': cv2.COLOR_BGR2HSV}
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if encoding not in conversions:
        # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
        raise ValueError(f'지원하지 않는 encoding: {encoding}')
    # cvtColor(입력 배열, 변환 코드)는 새 색 공간 배열을 반환한다. RGB2HSV와 BGR2HSV는 채널 해석이 다르다.
    return cv2.cvtColor(array, conversions[encoding])

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def main():
    p = parser(__doc__)
    # 실행 옵션을 정의한다. action=store_true는 옵션 유무를 bool로, type은 입력값 변환을, default는 생략 시 값을 지정한다.
    p.add_argument('--ros', action='store_true')
    # 실행 옵션을 정의한다. action=store_true는 옵션 유무를 bool로, type은 입력값 변환을, default는 생략 시 값을 지정한다.
    p.add_argument('--topic', default='/camera/camera/color/image_raw')
    # 터미널의 옵션을 읽어 객체로 반환한다. 예: --no-gui는 객체의 no_gui=True가 된다.
    a = p.parse_args()
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if a.ros and (a.camera or a.image):
        # 잘못된 옵션 조합의 이유를 출력하고 실행을 종료한다.
        p.error('--ros는 --camera 또는 --image와 함께 사용하지 않는다.')
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if a.ros:
        # 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
        import rclpy
        # 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
        from sensor_msgs.msg import Image
        # ROS 센서용 QoS 설정을 사용한다. 발행자와 구독자의 QoS가 맞지 않으면 영상이 수신되지 않을 수 있다.
        from rclpy.qos import qos_profile_sensor_data
        # 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
        from cv_bridge import CvBridge
        # 현재 프로세스의 ROS 통신 기능을 초기화한다.
        rclpy.init()
        # ROS 노드를 만든다. 노드 이름은 다른 노드와 구분할 수 있는 이름을 사용한다.
        node = rclpy.create_node('inspect_color_encoding')
        received = []
        # def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
        def callback(msg):
            # 리스트 끝에 원소 하나를 추가한다. 결과/후보를 순서대로 모은다.
            received.append(msg)
        # ROS 센서용 QoS 설정을 사용한다. 발행자와 구독자의 QoS가 맞지 않으면 영상이 수신되지 않을 수 있다.
        sub = node.create_subscription(Image, a.topic, callback, qos_profile_sensor_data)
        # 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
        import time
        # 시스템 시간 수정으로 거꾸로 가지 않는 시계를 사용한다. monotonic_ns는 ns 정수, monotonic은 초 단위 실수다.
        deadline = time.monotonic() + 10
        # 실패할 수 있는 작업을 시작한다. 대응하는 except는 오류 처리, finally는 성공·실패와 관계없는 정리다.
        try:
            # 시스템 시간 수정으로 거꾸로 가지 않는 시계를 사용한다. monotonic_ns는 ns 정수, monotonic은 초 단위 실수다.
            while not received and time.monotonic() < deadline and rclpy.ok():
                # ROS 콜백을 처리한다. timeout_sec는 한 번 기다릴 최대 시간이며 전체 수신 제한 시간은 별도로 검사한다.
                rclpy.spin_once(node, timeout_sec=.2)
            # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
            if not received:
                # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
                raise RuntimeError('10초간 영상 없음. topic 이름·ROS 환경·QoS를 확인한다.')
            msg = received[0]
            # CvBridge가 ROS Image를 배열로 변환한다. passthrough는 메시지의 채널 순서를 유지하므로 msg.encoding을 함께 확인해야 한다.
            frame = CvBridge().imgmsg_to_cv2(msg, desired_encoding='passthrough')
            encoding = msg.encoding
            # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
            print('header.frame_id=', msg.header.frame_id, 'stamp=', msg.header.stamp)
            # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
            print('step(bytes/row)=', msg.step, 'is_bigendian=', msg.is_bigendian)
        # try 블록을 어떤 경로로 빠져나와도 아래 정리 코드를 실행한다.
        finally:
            # 구독 등 노드 자원을 정리한다.
            node.destroy_node()
            # 현재 프로세스의 ROS 통신 컨텍스트를 종료한다.
            rclpy.shutdown()
    # 앞의 조건에 해당하지 않는 경우 이 블록을 실행한다.
    else:
        frame, stamp = read_once(a)
        encoding = 'bgr8'
        # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
        print('host_receive_monotonic_ns=', stamp)
    # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
    print('encoding=', encoding, 'dtype=', frame.dtype, 'shape=', frame.shape)
    hsv = to_hsv(frame, encoding)
    # cvtColor(입력 배열, 변환 코드)는 새 색 공간 배열을 반환한다. RGB2HSV와 BGR2HSV는 채널 해석이 다르다.
    rgb = frame if encoding == 'rgb8' else cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
    print('imageio에 전달할 RGB 배열:', rgb.shape, rgb.dtype)
    # 폴더를 만든다. parents=True는 상위 폴더도 생성하고 exist_ok=True는 이미 있어도 오류를 내지 않는다.
    a.out.mkdir(parents=True, exist_ok=True)
    # NumPy 배열을 .npy로 저장한다. 여기서는 imageio에 넘길 RGB 순서의 배열을 보관한다. PNG나 MP4 저장은 아니다.
    np.save(a.out / '03_imageio_RGB.npy', rgb)
    # cvtColor(입력 배열, 변환 코드)는 새 색 공간 배열을 반환한다. RGB2HSV와 BGR2HSV는 채널 해석이 다르다.
    bgr = frame if encoding == 'bgr8' else cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    # :는 해당 축 전체다. 세 번째 축의 0번 채널, 즉 H만 선택한다. 색상 배열을 그대로 imshow하지 않는다.
    show(a, {'03_display_BGR': bgr, '03_H_channel': hsv[:, :, 0]})

# 파일을 직접 실행할 때만 아래 블록을 수행한다. 다른 파일에서 import하면 이 블록은 실행하지 않는다.
if __name__ == '__main__':
    main()
