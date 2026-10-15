# 이 파일에서 읽어야 할 문법·계산
# if not devices는 리스트가 비었는지 확인한다. len(devices)는 장치 수다.
# A if condition else B는 조건식이다. supports(key)가 참일 때만 get_info(key)를 호출한다.
# started=False/True는 스트리밍 시작 성공 여부를 기억하는 bool이다. 시작 실패 후 불필요한 stop 호출을 막는다.
# raise만 쓰면 현재 처리 중인 예외를 다시 전달한다. 오류 문구 출력 후 실패 상태를 숨기지 않는다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""D435i 연결·장치 정보·컬러 수집. ROS 카메라 노드/Viewer를 종료한 뒤 실행한다."""
# 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
import argparse
# D435i SDK 바인딩을 rs라는 별명으로 불러온다. SDK가 필요한 실행 경로에서만 설치가 필요하다.
import pyrealsense2 as rs
# NumPy를 np라는 별명으로 불러온다. 영상은 숫자를 담은 다차원 배열이다.
import numpy as np

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def main():
    # 명령행 옵션을 해석할 객체를 만든다. description은 --help에 표시할 설명이다.
    p = argparse.ArgumentParser(description=__doc__)
    # 실행 옵션을 정의한다. action=store_true는 옵션 유무를 bool로, type은 입력값 변환을, default는 생략 시 값을 지정한다.
    p.add_argument('--serial', help='여러 카메라가 있으면 시리얼 번호 선택')
    # 터미널의 옵션을 읽어 객체로 반환한다. 예: --no-gui는 객체의 no_gui=True가 된다.
    args = p.parse_args()
    # 연결된 RealSense 장치를 열거한다. list()로 파이썬 리스트로 변환해 개수와 반복 처리를 쉽게 한다.
    devices = list(rs.context().query_devices())
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if not devices:
        # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
        raise SystemExit('장치를 찾지 못했다. USB 3 포트·케이블·권한을 확인한다.')
    # for는 목록/범위의 값을 하나씩 꺼내 반복한다. 쉼표로 묶인 변수에는 각 원소를 나누어 대입한다.
    for d in devices:
        # for는 목록/범위의 값을 하나씩 꺼내 반복한다. 쉼표로 묶인 변수에는 각 원소를 나누어 대입한다.
        for key in (rs.camera_info.name, rs.camera_info.serial_number, rs.camera_info.usb_type_descriptor):
            # 장치 정보를 문자열로 읽는다. supports(key)를 확인한 항목만 조회하며 지원하지 않으면 unknown을 사용한다.
            print(key, ':', d.get_info(key) if d.supports(key) else 'unknown')
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if len(devices) > 1 and not args.serial:
        # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
        raise SystemExit('여러 장치가 있다. --serial로 하나를 선택한다.')
    # 활성화할 장치와 영상 프로파일을 담는 설정 객체다.
    config = rs.config()
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if args.serial:
        # 시리얼 번호로 특정 장치를 선택한다. 여러 대 연결 시 임의 선택을 피한다.
        config.enable_device(args.serial)
    # 컬러 스트림·너비 640·높이 480·bgr8 형식·초당 30프레임을 요청한다. 장치/연결이 지원하지 않으면 시작 시 실패할 수 있다.
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    # 파이프라인은 장치의 스트림 시작·프레임 수집·종료를 관리한다.
    pipeline = rs.pipeline()
    started = False
    # 실패할 수 있는 작업을 시작한다. 대응하는 except는 오류 처리, finally는 성공·실패와 관계없는 정리다.
    try:
        # 요청한 프로파일로 실제 스트리밍을 시작한다. 점유·권한·USB·지원 프로파일 문제로 예외가 발생할 수 있다.
        pipeline.start(config)
        started = True
        # 새 프레임 묶음을 기다린다. get_color_frame은 그중 컬러 프레임만 선택한다.
        color = pipeline.wait_for_frames().get_color_frame()
        # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
        if not color:
            # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
            raise RuntimeError('컬러 프레임 없음')
        # SDK 프레임 버퍼를 NumPy 배열로 본다. copy()로 복사하면 다음 프레임 수신 후에도 현재 데이터가 유지된다.
        array = np.asanyarray(color.get_data())
        # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
        print('성공:', array.shape, array.dtype, 'encoding=bgr8')
        # SDK 프레임 번호와 타임스탬프를 출력한다. get_timestamp의 단위는 ms이며 호스트 monotonic 시각과 같은 기준이라고 가정하지 않는다.
        print('frame_number=', color.get_frame_number(), 'timestamp_ms=', color.get_timestamp())
    # 지정한 종류의 예외를 처리한다. as e는 예외 정보를 e라는 이름에 담는다.
    except RuntimeError as e:
        # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
        print('수집 실패:', e)
        # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
        print('점유 충돌이라고 단정하지 않는다. ROS 노드/Viewer 종료, USB 연결, 권한, 프로파일을 순서대로 확인한다.')
        raise
    # try 블록을 어떤 경로로 빠져나와도 아래 정리 코드를 실행한다.
    finally:
        # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
        if started:
            # SDK 스트리밍을 종료하고 장치 점유를 해제한다. 시작에 성공한 경우에만 호출한다.
            pipeline.stop()

# 파일을 직접 실행할 때만 아래 블록을 수행한다. 다른 파일에서 import하면 이 블록은 실행하지 않는다.
if __name__ == '__main__':
    main()
