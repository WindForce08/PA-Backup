# 이 파일에서 읽어야 할 문법·계산
# [함수(n) for n in names]는 리스트 내포다. 이름 목록을 차례로 읽어 트랙바 값 여섯 개를 만든다.
# values[:3]은 하한 H/S/V, values[3:]는 상한 H/S/V다. 슬라이스의 끝 위치는 제외한다.
# any(lo>hi for lo,hi in zip(...))는 여섯 값을 짝지어 하나라도 하한>상한인지 검사하는 생성기 표현식이다.
# lambda value: None은 인자 하나를 받지만 별도 동작하지 않는 콜백이다. 값은 getTrackbarPos로 직접 읽는다.
# H/S/V의 일반 uint8 범위는 각각 0~179, 0~255, 0~255다. HSV_FULL이나 float 변환에는 그대로 적용하지 않는다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""HSV 트랙바로 실제 파란색 범위를 조정한다. --no-gui는 시작 범위만 저장한다."""
# cv2는 OpenCV의 파이썬 모듈명이다. 설치할 때의 패키지 이름은 opencv-python이다.
import cv2
# NumPy를 np라는 별명으로 불러온다. 영상은 숫자를 담은 다차원 배열이다.
import numpy as np
# 같은 폴더의 common.py에서 이름을 가져온다. 카메라/파일 입출력과 저장을 재사용한다.
from common import parser, source, show

# 터미널의 옵션을 읽어 객체로 반환한다. 예: --no-gui는 객체의 no_gui=True가 된다.
a = parser(__doc__).parse_args()
names = ['H low', 'S low', 'V low', 'H high', 'S high', 'V high']
initial = [95, 80, 40, 130, 255, 255]
# 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
if not a.no_gui:
    # namedWindow는 지정한 이름의 창을 만든다. 트랙바를 이 창에 붙인다.
    cv2.namedWindow('HSV controls')
    # zip은 여러 목록의 같은 위치 원소를 묶는다. 가장 짧은 목록 길이까지만 반복한다.
    for name, value, maximum in zip(names, initial, [179,255,255,179,255,255]):
        # createTrackbar(이름, 창 이름, 시작값, 최대값, 콜백)는 슬라이더를 만든다. lambda는 이름 없는 함수이며 여기서는 별도 동작을 하지 않는다.
        cv2.createTrackbar(name, 'HSV controls', value, maximum, lambda value: None)
# 실패할 수 있는 작업을 시작한다. 대응하는 except는 오류 처리, finally는 성공·실패와 관계없는 정리다.
try:
    # with 블록 동안 자원을 사용한다. 중간에 예외가 나더라도 contextmanager의 정리 코드가 실행된다.
    with source(a) as read:
        # 조건이 참인 동안 반복한다. break는 반복 종료, continue는 다음 반복으로 이동이다.
        while True:
            frame, _ = read()
            # getTrackbarPos(이름, 창 이름)는 현재 슬라이더의 정수 값을 반환한다. 리스트 내포로 여섯 값을 한 번에 읽는다.
            values = initial if a.no_gui else [cv2.getTrackbarPos(n,'HSV controls') for n in names]
            # zip은 여러 목록의 같은 위치 원소를 묶는다. 가장 짧은 목록 길이까지만 반복한다.
            if any(lo > hi for lo,hi in zip(values[:3], values[3:])):
                # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
                print('하한이 상한보다 크다. 트랙바를 조정한다.')
                # waitKey는 GUI 이벤트를 처리하고 키 코드를 반환한다. 0은 키를 누를 때까지, 양수는 최소 대기 시간[ms]이다. & 0xFF는 하위 8비트, ord(q)는 q의 문자 코드다.
                if cv2.waitKey(30) & 0xFF in (27,ord('q')): break
                continue
            # cvtColor(입력 배열, 변환 코드)는 새 색 공간 배열을 반환한다. RGB2HSV와 BGR2HSV는 채널 해석이 다르다.
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # 리스트를 NumPy 배열로 만든다. uint8은 0~255 정수이며 int32는 부호 있는 32비트 정수다.
            mask = cv2.inRange(hsv, np.array(values[:3],np.uint8), np.array(values[3:],np.uint8))
            # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
            if a.no_gui:
                show(a, {'05_frame':frame, '05_mask':mask})
                break
            # imshow(창 이름, 영상)는 GUI 창에 배열을 표시한다. OpenCV 기본 컬러 표시는 BGR이며 이벤트 처리를 위해 waitKey가 필요하다.
            cv2.imshow('05 frame',frame)
            # imshow(창 이름, 영상)는 GUI 창에 배열을 표시한다. OpenCV 기본 컬러 표시는 BGR이며 이벤트 처리를 위해 waitKey가 필요하다.
            cv2.imshow('05 mask',mask)
            # waitKey는 GUI 이벤트를 처리하고 키 코드를 반환한다. 0은 키를 누를 때까지, 양수는 최소 대기 시간[ms]이다. & 0xFF는 하위 8비트, ord(q)는 q의 문자 코드다.
            if cv2.waitKey(30) & 0xFF in (27,ord('q')):
                # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
                print('선택 범위:', values[:3], values[3:])
                break
# try 블록을 어떤 경로로 빠져나와도 아래 정리 코드를 실행한다.
finally:
    # OpenCV가 만든 창을 모두 닫는다. 프로그램 종료 경로에서도 실행해 창이 남지 않게 한다.
    cv2.destroyAllWindows()
