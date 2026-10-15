# 이 파일에서 읽어야 할 문법·계산
# int(.1*w)는 영상 너비의 10% 위치를 정수로 만든다. ROI=(왼쪽,위,오른쪽,아래) 순서다.
# 0.5<=bw/bh<=2는 가로세로 비율의 양쪽 경계를 한 번에 확인하는 파이썬 연쇄 비교다.
# x+bw,y+bh는 박스의 제외 경계다. ROI 안에 박스 전체가 들어오는지 검사하며, 그릴 때는 -1로 마지막 포함 픽셀을 구한다.
# max(candidates,key=cv2.contourArea)는 넓이가 가장 큰 윤곽선 자체를 반환한다. 넓이 숫자를 반환하는 것이 아니다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""면적·ROI·가로세로 비율로 후보를 거르고 가장 큰 후보 하나를 선택한다."""
# cv2는 OpenCV의 파이썬 모듈명이다. 설치할 때의 패키지 이름은 opencv-python이다.
import cv2
# 같은 폴더의 common.py에서 이름을 가져온다. 카메라/파일 입출력과 저장을 재사용한다.
from common import parser, read_once, blue_mask, show

# def로 재사용할 함수를 정의한다. 괄호 안은 입력 인자이며 = 뒤 값은 생략 시 기본값이다. 들여쓴 본문은 호출할 때 실행된다.
def select(frame, min_area=500):
    mask = blue_mask(frame)
    # findContours(마스크, 검색 방식, 근사 방식)는 (윤곽선 목록, 계층 정보)를 반환한다. RETR_EXTERNAL은 바깥 윤곽선만, CHAIN_APPROX_SIMPLE은 직선의 중간 점을 줄인다. _는 사용하지 않을 반환값이다.
    contours, _ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    # shape는 배열 각 축의 길이다. [:2]는 앞 두 값 (높이, 너비)을 선택하며 h,w에 순서대로 대입한다.
    h,w = frame.shape[:2]
    roi = (int(.1*w),int(.1*h),int(.9*w),int(.9*h))
    candidates=[]
    # for는 목록/범위의 값을 하나씩 꺼내 반복한다. 쉼표로 묶인 변수에는 각 원소를 나누어 대입한다.
    for c in contours:
        # boundingRect(윤곽선)는 축에 평행한 사각형 (x,y,w,h)를 반환한다. x,y는 좌상단 픽셀, w,h는 크기다.
        x,y,bw,bh = cv2.boundingRect(c)
        # contourArea(윤곽선)는 연속 좌표 기반 면적을 반환한다. 단위는 픽셀²이며 흰 픽셀의 개수와 반드시 같지는 않다.
        area = cv2.contourArea(c)
        # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
        if area >= min_area and .5 <= bw/bh <= 2 and roi[0]<=x and roi[1]<=y and x+bw<=roi[2] and y+bh<=roi[3]:
            # 리스트 끝에 원소 하나를 추가한다. 결과/후보를 순서대로 모은다.
            candidates.append(c)
    # contourArea(윤곽선)는 연속 좌표 기반 면적을 반환한다. 단위는 픽셀²이며 흰 픽셀의 개수와 반드시 같지는 않다.
    selected = max(candidates,key=cv2.contourArea) if candidates else None
    # 계산 결과를 호출한 곳으로 돌려주고 함수를 끝낸다. 쉼표로 여러 값을 반환하면 튜플로 묶인다.
    return mask,roi,candidates,selected

# 파일을 직접 실행할 때만 아래 블록을 수행한다. 다른 파일에서 import하면 이 블록은 실행하지 않는다.
if __name__ == '__main__':
    # 터미널의 옵션을 읽어 객체로 반환한다. 예: --no-gui는 객체의 no_gui=True가 된다.
    a = parser(__doc__).parse_args()
    frame,_ = read_once(a)
    # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
    if not a.camera and not a.image:
        # rectangle(영상, 좌상단, 우하단, BGR색, 두께)는 입력 영상을 직접 바꾼다. 두께 -1은 내부 채움, (0,255,0)은 초록색이다.
        cv2.rectangle(frame,(30,30),(95,95),(255,0,0),-1) # ROI 바깥
        # rectangle(영상, 좌상단, 우하단, BGR색, 두께)는 입력 영상을 직접 바꾼다. 두께 -1은 내부 채움, (0,255,0)은 초록색이다.
        cv2.rectangle(frame,(100,100),(110,110),(255,0,0),-1) # 작은 잡음
        # rectangle(영상, 좌상단, 우하단, BGR색, 두께)는 입력 영상을 직접 바꾼다. 두께 -1은 내부 채움, (0,255,0)은 초록색이다.
        cv2.rectangle(frame,(430,340),(565,355),(255,0,0),-1) # 길쭉한 후보
    mask,roi,candidates,selected = select(frame)
    # 원본과 독립적인 배열 복사본을 만든다. overlay에 그림을 그려도 원본 증거 영상은 바뀌지 않는다.
    overlay = frame.copy()
    # rectangle(영상, 좌상단, 우하단, BGR색, 두께)는 입력 영상을 직접 바꾼다. 두께 -1은 내부 채움, (0,255,0)은 초록색이다.
    cv2.rectangle(overlay,roi[:2],roi[2:],(0,255,255),1)
    # None은 선택 결과가 없음을 나타낸다. NumPy 배열을 if selected로 검사하면 참/거짓이 모호하므로 is not None을 사용한다.
    if selected is not None:
        # boundingRect(윤곽선)는 축에 평행한 사각형 (x,y,w,h)를 반환한다. x,y는 좌상단 픽셀, w,h는 크기다.
        x,y,w,h = cv2.boundingRect(selected)
        # rectangle(영상, 좌상단, 우하단, BGR색, 두께)는 입력 영상을 직접 바꾼다. 두께 -1은 내부 채움, (0,255,0)은 초록색이다.
        cv2.rectangle(overlay,(x,y),(x+w-1,y+h-1),(0,255,0),2)
    # None은 선택 결과가 없음을 나타낸다. NumPy 배열을 if selected로 검사하면 참/거짓이 모호하므로 is not None을 사용한다.
    print('통과 후보 수=',len(candidates),'선택 여부=',selected is not None)
    # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
    print('형태 조건은 3D 큐브 인식이 아니다. 가림·원근 때문에 정상 물체도 제외될 수 있다.')
    show(a,{'06_overlay':overlay,'06_mask':mask})
