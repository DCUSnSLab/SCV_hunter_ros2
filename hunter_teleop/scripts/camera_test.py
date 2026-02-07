#!/usr/bin/env python3
"""카메라 테스트 - OpenCV로 카메라 영상 표시"""
import cv2
import sys

def main():
    device = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    cap = cv2.VideoCapture(device)
    if not cap.isOpened():
        print(f"[ERROR] /dev/video{device} 열 수 없음")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"[INFO] 카메라 {device} 연결됨. 'q'로 종료")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] 프레임 읽기 실패")
            break

        cv2.imshow('Camera Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
