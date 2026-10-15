# 이 파일에서 읽어야 할 문법·계산
# (cx-(W-1)/2)/(W/2)는 영상 중앙을 0으로 둔 수평 오차다. 오른쪽이 양수이며 단위가 없다.
# None if not detected else 식은 미검출일 때 정규화 오차도 무효로 둔다. 식 안의 center에 접근하지 않는다.
# tuple(map(round,center))는 표시용 중심을 가장 가까운 정수 픽셀로 바꾼다. 원본 실수 중심은 JSON에 유지한다.
# **state는 딕셔너리의 키·값을 새 딕셔너리에 펼친다. None은 JSON에서 null, False는 false로 저장된다.
# 같은 sample 문자열을 네 파일의 접두어로 써서 서로 다른 프레임의 원본과 mask가 섞이지 않게 한다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""같은 샘플 ID로 원본·mask·overlay·JSON을 저장한다."""
# 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
import importlib
# 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
import json
# 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
import uuid
# cv2는 OpenCV의 파이썬 모듈명이다. 설치할 때의 패키지 이름은 opencv-python이다.
import cv2
# 같은 폴더의 common.py에서 이름을 가져온다. 카메라/파일 입출력과 저장을 재사용한다.
from common import parser, read_once, blue_mask, save

# 문자열 파일명으로 모듈을 불러온다. 숫자로 시작하는 파일명은 일반 import 문으로 쓰기 어려워 이 방식을 사용한다.
detect=importlib.import_module('08_target_loss').detect
# 터미널의 옵션을 읽어 객체로 반환한다. 예: --no-gui는 객체의 no_gui=True가 된다.
a=parser(__doc__).parse_args()
frame,stamp=read_once(a)
state=detect(frame)
# shape는 배열 각 축의 길이다. [:2]는 앞 두 값 (높이, 너비)을 선택하며 h,w에 순서대로 대입한다.
h,w=frame.shape[:2]
error=None if not state['detected'] else (state['center'][0]-(w-1)/2)/(w/2)
# 원본과 독립적인 배열 복사본을 만든다. overlay에 그림을 그려도 원본 증거 영상은 바뀌지 않는다.
overlay=frame.copy()
mask=blue_mask(frame)
# 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
if state['detected']:
    # findContours(마스크, 검색 방식, 근사 방식)는 (윤곽선 목록, 계층 정보)를 반환한다. RETR_EXTERNAL은 바깥 윤곽선만, CHAIN_APPROX_SIMPLE은 직선의 중간 점을 줄인다. _는 사용하지 않을 반환값이다.
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    # contourArea(윤곽선)는 연속 좌표 기반 면적을 반환한다. 단위는 픽셀²이며 흰 픽셀의 개수와 반드시 같지는 않다.
    x,y,bw,bh=cv2.boundingRect(max(contours,key=cv2.contourArea))
    # rectangle(영상, 좌상단, 우하단, BGR색, 두께)는 입력 영상을 직접 바꾼다. 두께 -1은 내부 채움, (0,255,0)은 초록색이다.
    cv2.rectangle(overlay,(x,y),(x+bw-1,y+bh-1),(0,255,0),2)
    # circle(영상, 중심, 반지름, BGR색, 두께)는 입력 영상에 원을 그린다. 두께 -1은 원 내부를 채운다.
    cv2.circle(overlay,tuple(map(round,state['center'])),5,(0,255,0),-1)
lines=[f'host_rx_ns={stamp}',f'detected={state["detected"]} center={state["center"]}',f'ex_norm={error} reference={w}x{h}']
# enumerate는 순번과 값을 함께 반환한다. 시작값을 지정하지 않으면 번호는 0부터다.
for i,line in enumerate(lines):
    # putText(영상, 문자열, 시작점, 글꼴, 크기 배율, BGR색, 두께)는 입력 영상에 글자를 그린다. 기본 Hershey 글꼴은 한글에 적합하지 않아 그림 속 문자는 영문으로 표시한다.
    cv2.putText(overlay,line,(10,25+i*25),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,100,0),1)
# 임의 UUID 일부를 샘플 ID에 붙여 파일명 충돌 가능성을 줄인다.
sample=f'{stamp}_{uuid.uuid4().hex[:6]}'
# for는 목록/범위의 값을 하나씩 꺼내 반복한다. 쉼표로 묶인 변수에는 각 원소를 나누어 대입한다.
for suffix,image in [('original',frame),('mask',mask),('overlay',overlay)]:
    save(a.out/f'{sample}_{suffix}.png',image)
# dict는 이름:값을 묶는 딕셔너리를 만든다. **state는 기존 딕셔너리의 항목을 여기에 펼친다.
metadata=dict(sample_id=sample,source='D435i' if a.camera else str(a.image) if a.image else 'synthetic',host_receive_monotonic_ns=stamp,encoding='bgr8',coordinate_frame='color_image_pixels',width=w,height=h,normalized_error_x=error,**state)
# 파이썬 딕셔너리/리스트를 JSON 문자열로 바꾼다. ensure_ascii=False는 한글 유지, indent=2는 들여쓰기다.
(a.out/f'{sample}.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
# 파이썬 딕셔너리/리스트를 JSON 문자열로 바꾼다. ensure_ascii=False는 한글 유지, indent=2는 들여쓰기다.
print(json.dumps(metadata,ensure_ascii=False,indent=2))
# 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
print('시각은 호스트 수신 monotonic 시각이며 ROS header/카메라 노출 시각과 다르다.')
