# 이 파일에서 읽어야 할 문법·계산
# Path("results")는 경로 객체다. args.out / "a.png"는 파일 경로 연결이며 숫자 나눗셈이 아니다.
# np.full((480,640,3),220,np.uint8)의 튜플은 (행 수, 열 수, 채널 수)다. 같은 밝기 220을 세 채널에 넣으면 회색이다.
# read 함수 안에서 pipeline을 쓰는 것은 바깥 함수의 변수를 참조하는 클로저다. source가 with 블록 동안 장치의 수명을 관리한다.
# yield lambda: (frame.copy(), time.monotonic_ns())는 값을 즉시 읽는 대신 나중에 호출할 함수를 제공한다.
# tuple을 반환한 frame,stamp=read()는 두 반환값을 각각 변수에 나누어 대입하는 언패킹이다.
# dict.items()는 (키,값) 쌍을 반복한다. show의 키는 창 이름이자 저장 파일명이다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""공통 입출력만 모은다. 검출 알고리즘은 각 예제에서 확인한다."""
# 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
import argparse
# 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
from contextlib import contextmanager
# 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
from pathlib import Path
# 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
import time
# cv2는 OpenCV의 파이썬 모듈명이다. 설치할 때의 패키지 이름은 opencv-python이다.
import cv2
# NumPy를 np라는 별명으로 불러온다. 영상은 숫자를 담은 다차원 배열이다.
import numpy as np

# 리스트를 NumPy 배열로 만든다. uint8은 0~255 정수이며 int32는 부호 있는 32비트 정수다.
LOWER = np.array([95, 80, 40], np.uint8)
# 리스트를 NumPy 배열로 만든다. uint8은 0~255 정수이며 int32는 부호 있는 32비트 정수다.
UPPER = np.array([130, 255, 255], np.uint8)

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def parser(description):
    # 명령행 옵션을 해석할 객체를 만든다. description은 --help에 표시할 설명이다.
    p = argparse.ArgumentParser(description=description)
    # 이 그룹의 옵션은 동시에 선택할 수 없다. 카메라와 저장 이미지를 중복 지정하지 않게 한다.
    source = p.add_mutually_exclusive_group()
    # 실행 옵션을 정의한다. action=store_true는 옵션 유무를 bool로, type은 입력값 변환을, default는 생략 시 값을 지정한다.
    source.add_argument('--camera', action='store_true', help='D435i 컬러 영상 사용')
    # 실행 옵션을 정의한다. action=store_true는 옵션 유무를 bool로, type은 입력값 변환을, default는 생략 시 값을 지정한다.
    source.add_argument('--image', type=Path, help='저장된 영상 한 장 사용')
    # 실행 옵션을 정의한다. action=store_true는 옵션 유무를 bool로, type은 입력값 변환을, default는 생략 시 값을 지정한다.
    p.add_argument('--no-gui', action='store_true', help='창 없이 결과 저장')
    # 실행 옵션을 정의한다. action=store_true는 옵션 유무를 bool로, type은 입력값 변환을, default는 생략 시 값을 지정한다.
    p.add_argument('--out', type=Path, default=Path('results'))
    # 계산 결과를 호출한 곳으로 돌려주고 함수를 끝낸다. 쉼표로 여러 값을 반환하면 튜플로 묶인다.
    return p

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def synthetic(scene='clear'):
    # 지정한 shape 전체를 같은 값으로 채운다. (480,640,3)은 높이 480·너비 640·BGR 3채널이다.
    image = np.full((480, 640, 3), 220, np.uint8)
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if scene != 'empty':
        # rectangle(영상, 좌상단, 우하단, BGR색, 두께)는 입력 영상을 직접 바꾼다. 두께 -1은 내부 채움, (0,255,0)은 초록색이다.
        cv2.rectangle(image, (240, 150), (400, 310), (255, 0, 0), -1)
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if scene == 'occluded':
        # rectangle(영상, 좌상단, 우하단, BGR색, 두께)는 입력 영상을 직접 바꾼다. 두께 -1은 내부 채움, (0,255,0)은 초록색이다.
        cv2.rectangle(image, (325, 140), (420, 320), (220, 220, 220), -1)
    # putText(영상, 문자열, 시작점, 글꼴, 크기 배율, BGR색, 두께)는 입력 영상에 글자를 그린다. 기본 Hershey 글꼴은 한글에 적합하지 않아 그림 속 문자는 영문으로 표시한다.
    cv2.putText(image, 'SYNTHETIC - NOT A CAMERA CAPTURE', (10, 465),
                # putText의 이어지는 인자다. 글꼴·배율·색·두께를 지정한다. 영상 좌표는 좌상단이 원점이다.
                cv2.FONT_HERSHEY_SIMPLEX, .5, (30, 30, 30), 1)
    # 계산 결과를 호출한 곳으로 돌려주고 함수를 끝낸다. 쉼표로 여러 값을 반환하면 튜플로 묶인다.
    return image

# yield 앞을 준비, yield 뒤의 finally를 정리 과정으로 사용하는 with 문용 함수를 만든다.
@contextmanager
# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def source(args):
    """read()는 (BGR 배열, 호스트 수신 시각[ns])을 반환한다. 카메라 노출 시각과 다르다."""
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if args.camera:
        # D435i SDK 바인딩을 rs라는 별명으로 불러온다. SDK가 필요한 실행 경로에서만 설치가 필요하다.
        import pyrealsense2 as rs
        # 파이프라인은 장치의 스트림 시작·프레임 수집·종료를 관리한다.
        pipeline = rs.pipeline()
        # 활성화할 장치와 영상 프로파일을 담는 설정 객체다.
        config = rs.config()
        # 컬러 스트림·너비 640·높이 480·bgr8 형식·초당 30프레임을 요청한다. 장치/연결이 지원하지 않으면 시작 시 실패할 수 있다.
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        # 요청한 프로파일로 실제 스트리밍을 시작한다. 점유·권한·USB·지원 프로파일 문제로 예외가 발생할 수 있다.
        pipeline.start(config)
        # def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
        def read():
            # 새 프레임 묶음을 기다린다. get_color_frame은 그중 컬러 프레임만 선택한다.
            color = pipeline.wait_for_frames().get_color_frame()
            # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
            if not color:
                # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
                raise RuntimeError('컬러 프레임이 없다.')
            # SDK 프레임 버퍼를 NumPy 배열로 본다. copy()로 복사하면 다음 프레임 수신 후에도 현재 데이터가 유지된다.
            return np.asanyarray(color.get_data()).copy(), time.monotonic_ns()
        # 실패할 수 있는 작업을 시작한다. 대응하는 except는 오류 처리, finally는 성공·실패와 관계없는 정리다.
        try:
            # yield는 값을 with 블록에 제공한다. 블록이 끝나면 함수 실행이 이어져 자원을 정리한다.
            yield read
        # try 블록을 어떤 경로로 빠져나와도 아래 정리 코드를 실행한다.
        finally:
            # SDK 스트리밍을 종료하고 장치 점유를 해제한다. 시작에 성공한 경우에만 호출한다.
            pipeline.stop()
    # 앞의 조건에 해당하지 않는 경우 이 블록을 실행한다.
    else:
        # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
        if args.image:
            # imdecode(압축 파일 바이트 배열, IMREAD_COLOR)는 BGR uint8 영상으로 해독한다. 실패하면 None이다.
            frame = cv2.imdecode(np.frombuffer(args.image.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
            # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
            if frame is None:
                # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
                raise ValueError('이미지를 읽을 수 없다.')
        # 앞의 조건에 해당하지 않는 경우 이 블록을 실행한다.
        else:
            frame = synthetic()
        # 시스템 시간 수정으로 거꾸로 가지 않는 시계를 사용한다. monotonic_ns는 ns 정수, monotonic은 초 단위 실수다.
        yield lambda: (frame.copy(), time.monotonic_ns())

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def read_once(args):
    # with 블록 동안 자원을 사용한다. 중간에 예외가 나더라도 contextmanager의 정리 코드가 실행된다.
    with source(args) as read:
        # 계산 결과를 호출한 곳으로 돌려주고 함수를 끝낸다. 쉼표로 여러 값을 반환하면 튜플로 묶인다.
        return read()

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def blue_mask(frame):
    # cvtColor(입력 배열, 변환 코드)는 새 색 공간 배열을 반환한다. RGB2HSV와 BGR2HSV는 채널 해석이 다르다.
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # inRange(배열, 하한, 상한)는 모든 채널이 범위 안이면 255, 아니면 0인 uint8 이진 마스크를 반환한다. 경계값도 포함한다.
    mask = cv2.inRange(hsv, LOWER, UPPER)
    # 원소가 모두 1인 배열을 만든다. 5×5 커널은 형태학 연산에서 확인할 주변 영역이다.
    kernel = np.ones((5, 5), np.uint8)
    # MORPH_OPEN은 침식 후 팽창이다. 커널보다 작은 점 잡음을 줄이지만 작은 대상도 사라질 수 있다.
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # MORPH_CLOSE는 팽창 후 침식이다. 작은 구멍을 메우지만 가까운 물체가 연결될 수도 있다.
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def save(path, image):
    path = Path(path)
    # 폴더를 만든다. parents=True는 상위 폴더도 생성하고 exist_ok=True는 이미 있어도 오류를 내지 않는다.
    path.parent.mkdir(parents=True, exist_ok=True)
    # imencode(확장자, 영상)는 (성공 여부, 압축 바이트 배열)을 반환한다. 파일 쓰기를 Path에 맡겨 Windows 한글 경로도 처리한다.
    ok, data = cv2.imencode('.png', image)
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if not ok:
        # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
        raise RuntimeError('PNG 인코딩 실패')
    # 인코딩된 바이트를 파일에 쓴다. tobytes()는 NumPy 바이트 배열을 bytes로 바꾼다.
    path.write_bytes(data.tobytes())

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def show(args, images):
    # for는 목록/범위의 값을 하나씩 꺼내 반복한다. 쉼표로 묶인 변수에는 각 원소를 나누어 대입한다.
    for name, image in images.items():
        save(args.out / (name + '.png'), image)
        # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
        if not args.no_gui:
            # imshow(창 이름, 영상)는 GUI 창에 배열을 표시한다. OpenCV 기본 컬러 표시는 BGR이며 이벤트 처리를 위해 waitKey가 필요하다.
            cv2.imshow(name, image)
    # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
    print('저장 위치:', args.out.resolve())
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if not args.no_gui:
        # waitKey는 GUI 이벤트를 처리하고 키 코드를 반환한다. 0은 키를 누를 때까지, 양수는 최소 대기 시간[ms]이다. & 0xFF는 하위 8비트, ord(q)는 q의 문자 코드다.
        cv2.waitKey(0)
        # OpenCV가 만든 창을 모두 닫는다. 프로그램 종료 경로에서도 실행해 창이 남지 않게 한다.
        cv2.destroyAllWindows()
