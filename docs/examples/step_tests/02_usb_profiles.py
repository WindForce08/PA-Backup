# 이 파일에서 읽어야 할 문법·계산
# profiles=set()은 중복을 제거하는 집합이다. (너비,높이,FPS,형식) 튜플은 묶음 값이며 집합에 넣을 수 있다.
# f 문자열에서 {width:4}는 최소 4칸 오른쪽 정렬, {height:<4}는 최소 4칸 왼쪽 정렬이다.
# get_stream_profiles의 프로파일은 실제 실행 결과가 아니다. 노출된 조합 중 원하는 요청이 시작 가능한지는 01번처럼 별도 실행한다.

# 상세 주석판 — 들여쓰기는 실행 범위를, # 뒤의 글은 실행되지 않는 설명을 뜻한다.
# 좌표 (x,y)는 (열,행), NumPy 인덱스는 [행,열]이다. 컬러 배열은 H×W×3이다.
# = 는 대입, == 는 값 비교, is None은 결과 없음 검사다. 함수 호출은 이름(인자) 형태다.
"""현재 연결의 USB 정보와 장치가 노출하는 컬러 프로파일을 나열한다."""
# D435i SDK 바인딩을 rs라는 별명으로 불러온다. SDK가 필요한 실행 경로에서만 설치가 필요하다.
import pyrealsense2 as rs

# 연결된 RealSense 장치를 열거한다. list()로 파이썬 리스트로 변환해 개수와 반복 처리를 쉽게 한다.
devices = list(rs.context().query_devices())
# 조건이 참일 때만 들여쓴 코드를 실행한다. and는 모두 참, or는 하나 이상 참, not은 참/거짓 반전이다.
if not devices:
    # 예외를 발생시켜 조건이 잘못된 상태에서 다음 처리를 계속하지 않게 한다.
    raise SystemExit('RealSense 장치가 없다.')
# for는 목록/범위의 값을 하나씩 꺼내 반복한다. 쉼표로 묶인 변수에는 각 원소를 나누어 대입한다.
for device in devices:
    # 장치 정보를 문자열로 읽는다. supports(key)를 확인한 항목만 조회하며 지원하지 않으면 unknown을 사용한다.
    print('\nSERIAL:', device.get_info(rs.camera_info.serial_number))
    key = rs.camera_info.usb_type_descriptor
    # 장치 정보를 문자열로 읽는다. supports(key)를 확인한 항목만 조회하며 지원하지 않으면 unknown을 사용한다.
    print('USB:', device.get_info(key) if device.supports(key) else 'unknown')
    # set은 중복 없는 집합이다. 같은 너비·높이·FPS·형식 조합을 한 번만 출력한다.
    profiles = set()
    # for는 목록/범위의 값을 하나씩 꺼내 반복한다. 쉼표로 묶인 변수에는 각 원소를 나누어 대입한다.
    for sensor in device.query_sensors():
        # 센서가 제공하는 스트림 프로파일 목록을 얻는다. 이 목록 자체는 실제 수집 FPS 측정 결과가 아니다.
        for profile in sensor.get_stream_profiles():
            # 컬러 스트림인지, 너비·높이가 있는 영상 프로파일인지 확인한다. and는 두 조건이 모두 참이어야 한다.
            if profile.stream_type() == rs.stream.color and profile.is_video_stream_profile():
                # 일반 스트림 프로파일을 영상 프로파일로 해석해 width/height에 접근한다.
                v = profile.as_video_stream_profile()
                # 집합에 값을 추가한다. 같은 값이 이미 있으면 중복 저장되지 않는다.
                profiles.add((v.width(), v.height(), profile.fps(), str(profile.format())))
    # sorted는 정렬된 새 리스트를 반환한다. 튜플은 첫 값부터 차례대로 비교한다.
    for width, height, fps, fmt in sorted(profiles):
        # 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
        print(f'{width:4}x{height:<4} {fps:3} fps  {fmt}')
# 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
print('\nUSB 3/USB 2 연결에서 각각 저장해 비교한다. 목록의 FPS는 지원 프로파일이며 실측 FPS가 아니다.')
# 중간값이나 판정 결과를 터미널에 출력한다. 영상 창과 달리 SSH에서도 이 출력은 확인할 수 있다.
print('USB 2에서 무조건 특정 FPS가 된다고 가정하지 않는다. 다른 센서와의 동시 활성화 제약도 별도 확인한다.')
