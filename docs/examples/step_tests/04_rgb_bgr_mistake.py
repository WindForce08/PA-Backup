# 이 파일에서 읽어야 할 문법·계산
# [[[255,0,0]]]은 높이 1·너비 1·채널 3의 배열을 만들기 위해 대괄호가 세 겹이다.
# [0,0,0]은 첫 행·첫 열·H 채널을 선택한다. 같은 저장값을 BGR과 RGB로 해석하면 색 의미가 달라진다.
# cv2.inRange 결과는 HSV 영상 자체가 아니라 한 채널 이진 마스크다. 흰색은 조건에 맞는 픽셀을 뜻한다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""동일 배열을 BGR/RGB로 다르게 해석했을 때 H와 파란색 마스크를 비교한다."""
# cv2는 OpenCV의 파이썬 모듈명이다. 설치할 때의 패키지 이름은 opencv-python이다.
import cv2
# NumPy를 np라는 별명으로 불러온다. 영상은 숫자를 담은 다차원 배열이다.
import numpy as np
# 같은 폴더의 common.py에서 이름을 가져온다. 카메라/파일 입출력과 저장을 재사용한다.
from common import parser, read_once, show, LOWER, UPPER

# 터미널의 옵션을 읽어 객체로 반환한다. 예: --no-gui는 객체의 no_gui=True가 된다.
a = parser(__doc__).parse_args()
frame, _ = read_once(a)
# cvtColor(입력 배열, 변환 코드)는 새 색 공간 배열을 반환한다. RGB2HSV와 BGR2HSV는 채널 해석이 다르다.
correct = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
# cvtColor(입력 배열, 변환 코드)는 새 색 공간 배열을 반환한다. RGB2HSV와 BGR2HSV는 채널 해석이 다르다.
wrong = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)  # 의도적인 오류
# 리스트를 NumPy 배열로 만든다. uint8은 0~255 정수이며 int32는 부호 있는 32비트 정수다.
pixel = np.array([[[255, 0, 0]]], np.uint8)
# cvtColor(입력 배열, 변환 코드)는 새 색 공간 배열을 반환한다. RGB2HSV와 BGR2HSV는 채널 해석이 다르다.
print('BGR 파랑 [255,0,0]: 올바른 H=', cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)[0,0,0],
      # cvtColor(입력 배열, 변환 코드)는 새 색 공간 배열을 반환한다. RGB2HSV와 BGR2HSV는 채널 해석이 다르다.
      'RGB로 오해한 H=', cv2.cvtColor(pixel, cv2.COLOR_RGB2HSV)[0,0,0])
# 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
print('모양·dtype가 같아도 채널 의미는 다르다. encoding 또는 SDK 요청 포맷으로 확인한다.')
show(a, {'04_original': frame,
         # inRange(배열, 하한, 상한)는 모든 채널이 범위 안이면 255, 아니면 0인 uint8 이진 마스크를 반환한다. 경계값도 포함한다.
         '04_correct_mask': cv2.inRange(correct, LOWER, UPPER),
         # inRange(배열, 하한, 상한)는 모든 채널이 범위 안이면 255, 아니면 0인 uint8 이진 마스크를 반환한다. 경계값도 포함한다.
         '04_wrong_mask': cv2.inRange(wrong, LOWER, UPPER)})
