"""실제 장비에 접근하지 않고 합성 영상 경로와 중요한 실패 조건을 검사한다."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import cv2
import numpy as np
from common import synthetic

# import_module은 숫자로 시작하는 파일명도 문자열로 불러올 수 있다.
encoding = importlib.import_module('03_encoding_dtype_shape')
moments = importlib.import_module('07_moments_zero')
loss = importlib.import_module('08_target_loss')
candidate = importlib.import_module('06_candidate_selection')

# shape와 dtype는 같아도 채널 순서가 틀리면 다른 H가 나온다.
blue = np.array([[[255, 0, 0]]], np.uint8)
assert encoding.to_hsv(blue, 'bgr8')[0,0,0] == 120
assert encoding.to_hsv(blue, 'rgb8')[0,0,0] == 0
try:
    encoding.to_hsv(np.zeros((2,2),np.uint8),'mono8')
except ValueError:
    pass
else:
    raise AssertionError('비지원 형식을 거부해야 한다.')

# 작은 면적·가림·미검출을 큰 외부 의존성 없이 직접 확인한다.
line=np.array([[[10,10]],[[20,20]],[[30,30]]],np.int32)
assert moments.center(line) is None
assert loss.detect(synthetic('clear'))['detected']
assert loss.detect(synthetic('empty'))['center'] is None
assert loss.detect(synthetic('occluded'))['detected']
assert candidate.select(synthetic())[3] is not None
assert candidate.select(synthetic('empty'))[3] is None

# 임시 폴더에서 각 파일을 별도 Python 프로세스로 실행해 독립 실행 여부를 확인한다.
root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as folder:
    for path in sorted(root.glob('[0-9][0-9]_*.py')):
        n=int(path.name[:2])
        if n<3:
            continue  # 01·02는 실제 D435i가 필요하다.
        args=[sys.executable,str(path)]
        destination=Path(folder)/str(n)
        if n!=7:
            args += ['--no-gui','--out',str(destination)]
        subprocess.run(args,cwd=root,check=True,timeout=20,capture_output=True)
        if n==9:
            record=json.loads(next(destination.glob('*.json')).read_text(encoding='utf-8'))
            assert record['detected'] and record['distance_m'] is None
            for suffix in ['original','mask','overlay']:
                assert (destination/f'{record["sample_id"]}_{suffix}.png').is_file()
        if n==11:
            rows=json.loads((destination/'11_results.json').read_text(encoding='utf-8'))
            assert [row['verdict'] for row in rows]==['TP','TN','TP']
        print('PASS',path.name)
print('PASS: 합성 경로 9개·색 순서·지원 형식·m00=0·소실·후보 선택·좌표 복원·증거 저장')
