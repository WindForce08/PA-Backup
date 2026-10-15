# 이 파일에서 읽어야 할 문법·계산
# range(10)은 0~9까지 10회 반복한다. _는 반복 번호를 사용하지 않는다는 관례적인 이름이다.
# expected=scene!="empty"는 명확한 물체와 일부가 보이는 가림 장면을 양성으로 정의한다.
# detected와 expected의 두 bool을 비교해 TP/FP/FN/TN을 구분한다. 부분 가림의 중심은 보이는 영역 중심으로 이동할 수 있다.
# json 파일은 장면별 판정을 기록한다. 실제 입력 장면을 준비하는 책임까지 자동 검증하지는 않는다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""명확한 물체·빈 배경·부분 가림의 검출 결과를 비교한다."""
# 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
import importlib
# 표준 라이브러리 또는 외부 모듈에서 필요한 이름을 불러온다. 불러온 이름으로 아래 기능을 사용한다.
import json
# 같은 폴더의 common.py에서 이름을 가져온다. 카메라/파일 입출력과 저장을 재사용한다.
from common import parser, source, synthetic, save

# 문자열 파일명으로 모듈을 불러온다. 숫자로 시작하는 파일명은 일반 import 문으로 쓰기 어려워 이 방식을 사용한다.
detect=importlib.import_module('08_target_loss').detect
# 터미널의 옵션을 읽어 객체로 반환한다. 예: --no-gui는 객체의 no_gui=True가 된다.
a=parser(__doc__).parse_args()
rows=[]
# with 블록 동안 자원을 사용한다. 중간에 예외가 나더라도 contextmanager의 정리 코드가 실행된다.
with source(a) as read:
    # for는 목록/범위의 값을 하나씩 꺼내 반복한다. 쉼표로 묶인 변수에는 각 원소를 나누어 대입한다.
    for scene in ['clear','empty','occluded']:
        # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
        if a.camera:
            # 터미널에서 Enter 입력을 기다린다. 카메라 앞의 장면을 준비할 시간을 확보한다.
            input(f'{scene} 장면을 준비하고 Enter: ')
            # 준비 전 큐의 프레임을 버리고 새 프레임을 받는다.
            # for는 목록/범위의 값을 하나씩 꺼내 반복한다. 쉼표로 묶인 변수에는 각 원소를 나누어 대입한다.
            for _ in range(10):frame,stamp=read()
        # 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
        elif a.image:
            # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
            raise ValueError('세 장면 비교에는 기본 합성 영상 또는 --camera를 사용한다.')
        # 앞의 조건에 해당하지 않는 경우 이 블록을 실행한다.
        else:
            frame=synthetic(scene)
        result=detect(frame)
        expected=scene!='empty'
        verdict=('TP' if expected else 'FP') if result['detected'] else ('FN' if expected else 'TN')
        # dict는 이름:값을 묶는 딕셔너리를 만든다. **state는 기존 딕셔너리의 항목을 여기에 펼친다.
        rows.append(dict(scene=scene,expected_visible=expected,verdict=verdict,**result))
        save(a.out/f'11_{scene}.png',frame)
# 폴더를 만든다. parents=True는 상위 폴더도 생성하고 exist_ok=True는 이미 있어도 오류를 내지 않는다.
a.out.mkdir(parents=True,exist_ok=True)
# 파이썬 딕셔너리/리스트를 JSON 문자열로 바꾼다. ensure_ascii=False는 한글 유지, indent=2는 들여쓰기다.
(a.out/'11_results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
# for는 목록/범위의 값을 하나씩 꺼내 반복한다. 쉼표로 묶인 변수에는 각 원소를 나누어 대입한다.
for row in rows:print(row)
# 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
print('TP=정검출, FP=오검출, FN=미검출, TN=정상 비검출. 일부가 보이는 부분 가림을 준비한다.')
# 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
print('3장은 기능 확인용이다. 일반적인 정확도·성능을 입증하는 데이터셋은 아니다.')
