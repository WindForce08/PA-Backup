# 이 파일에서 읽어야 할 문법·계산
# crop=frame[y0:y1,x0:x1]에서 끝 인덱스는 포함하지 않는다. 따라서 crop의 크기는 y1-y0, x1-x0다.
# sx=small_width/crop_width와 sy=small_height/crop_height는 실제 출력 크기로 계산한 배율이다. 홀수 해상도의 반올림도 반영한다.
# (u+0.5)/sx-0.5+x0는 픽셀 중심 기준 역변환이다. 단순 좌표/스케일 규약과 섞지 않고 정방향도 같은 규약으로 검사한다.
# np.allclose는 실수 반올림 오차를 고려해 비교한다. 정확한 ==만 쓰면 수치 오차 때문에 검사가 실패할 수 있다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""crop과 축소 영상의 중심을 원본 좌표로 복원한다. 픽셀 중심 규약을 사용한다."""
# cv2는 OpenCV의 파이썬 모듈명이다. 설치할 때의 패키지 이름은 opencv-python이다.
import cv2
# NumPy를 np라는 별명으로 불러온다. 영상은 숫자를 담은 다차원 배열이다.
import numpy as np
# 같은 폴더의 common.py에서 이름을 가져온다. 카메라/파일 입출력과 저장을 재사용한다.
from common import parser, read_once, show

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def restore(u,v,scale_x,scale_y,x0,y0):
    # 계산 결과를 호출한 곳으로 돌려주고 함수를 끝낸다. 쉼표로 여러 값을 반환하면 튜플로 묶인다.
    return ((u+.5)/scale_x-.5+x0,(v+.5)/scale_y-.5+y0)

# 터미널의 옵션을 읽어 객체로 반환한다. 예: --no-gui는 객체의 no_gui=True가 된다.
a=parser(__doc__).parse_args()
frame,_=read_once(a)
# shape는 배열 각 축의 길이다. [:2]는 앞 두 값 (높이, 너비)을 선택하며 h,w에 순서대로 대입한다.
h,w=frame.shape[:2]
# 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
if h<4 or w<4:
    # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
    raise ValueError('좌표 비교에는 가로·세로 4픽셀 이상의 영상이 필요하다.')
x0,y0=int(.1*w),int(.1*h)
# NumPy 슬라이싱은 [행 범위, 열 범위] 즉 [y, x] 순서다. 끝 인덱스는 포함하지 않는다.
crop=frame[y0:int(.9*h),x0:int(.9*w)]
# resize(영상, 출력 크기, fx, fy, interpolation)는 크기가 바뀐 새 배열을 반환한다. None은 배율 사용, INTER_NEAREST는 가까운 픽셀 선택이다.
small=cv2.resize(crop,None,fx=.5,fy=.5,interpolation=cv2.INTER_NEAREST)
sx,sy=small.shape[1]/crop.shape[1],small.shape[0]/crop.shape[0]
u,v=(small.shape[1]-1)/2,(small.shape[0]-1)/2
x,y=restore(u,v,sx,sy,x0,y0)
# 원본과 독립적인 배열 복사본을 만든다. overlay에 그림을 그려도 원본 증거 영상은 바뀌지 않는다.
overlay=frame.copy()
# drawMarker(영상, 중심, BGR색, 마커 종류, 크기, 두께)는 지정 위치에 십자 등을 그린다. 좌표는 정수 픽셀로 전달한다.
cv2.drawMarker(overlay,(round(x),round(y)),(0,255,0),cv2.MARKER_CROSS,24,2)
# drawMarker(영상, 중심, BGR색, 마커 종류, 크기, 두께)는 지정 위치에 십자 등을 그린다. 좌표는 정수 픽셀로 전달한다.
cv2.drawMarker(overlay,(round(u),round(v)),(0,0,255),cv2.MARKER_TILTED_CROSS,24,2)
# 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
print('축소 중심=',(u,v),'원본 복원=',(x,y),'crop offset=',(x0,y0),'scale=',(sx,sy))
# 두 숫자 묶음이 부동소수점 오차 범위에서 같은지 검사한다. 좌표 복원의 역변환을 검증한다.
assert np.allclose(((x-x0+.5)*sx-.5,(y-y0+.5)*sy-.5),(u,v))
# 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
print('초록: 복원한 원본 좌표 / 빨강: 축소 좌표를 그대로 사용한 오류. 좌표 원점은 좌상단, x→오른쪽, y→아래다.')
show(a,{'10_overlay':overlay,'10_small':small})
