# 이 파일에서 읽어야 할 문법·계산
# [c for c in contours if 조건]은 조건에 맞는 윤곽선만 남기는 리스트 내포다.
# state["center"] if state["detected"] else last는 소실 시 이전 좌표를 쓰는 의도적인 잘못된 예다.
# tuple(map(int,stale))는 두 실수 좌표에 int를 적용하고 튜플로 묶는다. 이는 그림용 픽셀 좌표 변환이다.
# 검출 데이터 state의 center는 소실 때 None이며, stale 변수와 분리되어 있다. 이 파일은 모터 명령을 보내지 않는다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""검출→소실→재검출에서 직전 중심을 재사용하는 오류를 비교한다. 모터는 움직이지 않는다."""
# cv2는 OpenCV의 파이썬 모듈명이다. 설치할 때의 패키지 이름은 opencv-python이다.
import cv2
# 같은 폴더의 common.py에서 이름을 가져온다. 카메라/파일 입출력과 저장을 재사용한다.
from common import parser, synthetic, blue_mask, show

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def detect(frame):
    # findContours(마스크, 검색 방식, 근사 방식)는 (윤곽선 목록, 계층 정보)를 반환한다. RETR_EXTERNAL은 바깥 윤곽선만, CHAIN_APPROX_SIMPLE은 직선의 중간 점을 줄인다. _는 사용하지 않을 반환값이다.
    contours,_=cv2.findContours(blue_mask(frame),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    # contourArea(윤곽선)는 연속 좌표 기반 면적을 반환한다. 단위는 픽셀²이며 흰 픽셀의 개수와 반드시 같지는 않다.
    contours=[c for c in contours if cv2.contourArea(c)>=500]
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if not contours:
        # 계산 결과를 호출한 곳으로 돌려주고 함수를 끝낸다. 쉼표로 여러 값을 반환하면 튜플로 묶인다.
        return {'detected':False,'center':None,'distance_m':None}
    # contourArea(윤곽선)는 연속 좌표 기반 면적을 반환한다. 단위는 픽셀²이며 흰 픽셀의 개수와 반드시 같지는 않다.
    m=cv2.moments(max(contours,key=cv2.contourArea))
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if not m['m00']:
        # 계산 결과를 호출한 곳으로 돌려주고 함수를 끝낸다. 쉼표로 여러 값을 반환하면 튜플로 묶인다.
        return {'detected':False,'center':None,'distance_m':None}
    # 계산 결과를 호출한 곳으로 돌려주고 함수를 끝낸다. 쉼표로 여러 값을 반환하면 튜플로 묶인다.
    return {'detected':True,'center':(m['m10']/m['m00'],m['m01']/m['m00']),'distance_m':None}

# 파일을 직접 실행할 때만 아래 블록을 수행한다. 다른 파일에서 import하면 이 블록은 실행하지 않는다.
if __name__=='__main__':
    # 터미널의 옵션을 읽어 객체로 반환한다. 예: --no-gui는 객체의 no_gui=True가 된다.
    a=parser(__doc__).parse_args()
    last=None
    images={}
    # enumerate는 순번과 값을 함께 반환한다. 시작값을 지정하지 않으면 번호는 0부터다.
    for i,scene in enumerate(['clear','empty','clear']):
        frame=synthetic(scene)
        state=detect(frame)
        stale=state['center'] if state['detected'] else last
        # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
        print(i,scene,'정상:',state,'잘못된 재사용=',stale)
        # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
        if stale is not None:
            # drawMarker(영상, 중심, BGR색, 마커 종류, 크기, 두께)는 지정 위치에 십자 등을 그린다. 좌표는 정수 픽셀로 전달한다.
            cv2.drawMarker(frame,tuple(map(int,stale)),(0,0,255),cv2.MARKER_TILTED_CROSS,24,2)
        last=stale
        images[f'08_{i}_{scene}']=frame
        # 조건이 참인지 검사하는 검증문이다. 거짓이면 AssertionError가 발생한다. 카메라의 정상 동작을 대신 보장하지는 않는다.
        if scene=='empty':assert not state['detected'] and state['center'] is None
    # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
    print('빨간 표시는 잘못 재사용한 중심이다. distance_m은 깊이를 측정하지 않아 항상 None이다.')
    show(a,images)
