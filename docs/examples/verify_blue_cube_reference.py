"""파란색 기준 예제를 합성 영상으로 검증한다. 실제 카메라 검증은 별도다."""
from pathlib import Path
import cv2
import numpy as np
from blue_cube_reference import detect_blue

frame=np.full((480,640,3),230,np.uint8)
cv2.rectangle(frame,(230,140),(390,300),(255,0,0),-1)
cv2.rectangle(frame,(40,40),(150,150),(0,0,255),-1)
frame[20:23,20:23]=(255,0,0)
result,mask,boxes=detect_blue(frame)
assert boxes==[(230,140,161,161)],boxes
assert tuple(result[140,230])==(0,255,0)
assert not detect_blue(np.zeros_like(frame))[2]
cv2.putText(result,'SYNTHETIC EXAMPLE - NOT A CAMERA CAPTURE',(12,455),
            cv2.FONT_HERSHEY_SIMPLEX,.52,(30,30,30),1)
for name,image in [('blue_cube_synthetic.png',result),('blue_mask_synthetic.png',mask)]:
    ok,encoded=cv2.imencode('.png',image)
    assert ok
    target=Path(__file__).with_name(name)
    target.write_bytes(encoded.tobytes())
    assert target.stat().st_size>0
print('PASS: blue target, red rejection, noise removal, empty frame, green box')
