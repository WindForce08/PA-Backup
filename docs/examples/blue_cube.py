"""D435i 컬러 영상에서 파란색 후보를 찾고 초록색 박스를 그린다."""
import argparse
import cv2
import numpy as np

# OpenCV의 8비트 HSV: H=0~179, S/V=0~255. 조명에 맞춰 조정한다.
LOWER_BLUE = np.array([15, 100, 100], dtype=np.uint8)
UPPER_BLUE = np.array([35, 255, 255], dtype=np.uint8)
MIN_AREA = 500  # 픽셀 면적: 작은 파란색 잡음을 제외한다.


def detect_blue(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_BLUE, UPPER_BLUE)
    kernel = np.ones((5, 5), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours
             if cv2.contourArea(c) >= MIN_AREA]
    result = frame.copy()
    for x, y, w, h in boxes:
        cv2.rectangle(result, (x, y), (x + w - 1, y + h - 1),
                      (0, 255, 0), 2)  # BGR: 초록색
        cv2.putText(result, 'BLUE', (x, max(18, y - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return result, mask, boxes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--webcam', type=int, help='일반 웹캠 번호. 생략하면 D435i')
    args = parser.parse_args()
    pipeline = None
    cap = None
    started = False
    try:
        if args.webcam is None:
            import pyrealsense2 as rs
            pipeline = rs.pipeline()
            config = rs.config()
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            pipeline.start(config)
            started = True
        else:
            cap = cv2.VideoCapture(args.webcam)
            if not cap.isOpened():
                raise RuntimeError('카메라를 열 수 없다. 번호·USB 연결·점유를 확인한다.')

        while True:
            if pipeline is not None:
                frames = pipeline.wait_for_frames()
                color = frames.get_color_frame()
                if not color:
                    continue
                frame = np.asanyarray(color.get_data())
            else:
                ok, frame = cap.read()
                if not ok:
                    raise RuntimeError('카메라 프레임을 읽지 못했다.')
            result, mask, _ = detect_blue(frame)
            cv2.imshow('Blue cube - green box', result)
            cv2.imshow('Blue mask', mask)
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break
    finally:
        if pipeline is not None and started:
            pipeline.stop()
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
