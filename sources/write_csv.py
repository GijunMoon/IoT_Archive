import cv2
import csv
import os
from collections import defaultdict
from picamera2 import Picamera2
from ultralytics import YOLO
import time
import threading

# Picamera2 초기화 및 구성
picam2 = Picamera2()
picam2.preview_configuration.main.size = (1280, 720)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

# YOLOv8 모델 로드
model = YOLO("best (3).pt")

# CSV 파일 경로 설정
csv_file_path = 'detections.csv'

# class 이름을 list 형태로 저장
object_names = ['adult', 'kids']

# CSV 파일에 쓰기
def write_dict_to_csv(csv_file_path, detections):
    """
    CSV 파일에 객체 이름과 신뢰도 점수를 저장하는 함수
    :param csv_file_path: CSV 파일 경로
    :param detections: 객체 이름과 신뢰도 점수를 포함한 딕셔너리
    """
    file_exists = os.path.isfile(csv_file_path)  # 파일 존재 여부 확인
    write_header = not file_exists or os.stat(csv_file_path).st_size == 0  # 파일이 없거나 비어 있으면 헤더 작성

    with open(csv_file_path, mode='a', newline='') as outfile:  # 덧붙이기 모드로 파일 열기
        writer = csv.writer(outfile)
        
        # 첫 번째 라인에 헤더를 기록 (한 번만 실행)
        if write_header:
            writer.writerow(['Name', 'Confidence'])
        
        # 객체의 이름과 신뢰도 점수 기록
        for name, confidence in detections.items():
            if confidence <= 0.5:
                confidence = 'N/A'  # 신뢰도 점수가 0.5 이하일 경우 'N/A'로 표시
            writer.writerow([name, confidence])

# 객체 인식 후 결과 처리를 위한 함수
def process_result_and_update_csv(results, output_csv_path):
    current_detections = defaultdict(float)  # 감지 결과를 위한 기본값은 0.0

    # YOLO 결과에서 박스 정보 추출
    for result in results:
        boxes = result.boxes
        if not boxes:
            continue

        for box in boxes:
            class_id = int(box.cls)  # 클래스 ID 추출
            name = object_names[class_id]  # 클래스 ID를 사용하여 객체 이름 추출
            confidence = float(box.conf)  # 신뢰도 점수 추출
            
            if confidence > 0.5:  # 신뢰도 점수가 0.5 초과일 경우만 기록
                current_detections[name] = max(current_detections.get(name, 0), confidence)

    # CSV 파일에 객체 이름, 신뢰도 점수 저장
    write_dict_to_csv(output_csv_path, current_detections)

# 스트리밍 제어용 플래그와 스레드 이벤트 객체
streaming_active = False
streaming_event = threading.Event()

def start_streaming():
    global streaming_active
    streaming_active = True
    streaming_event.set()  # 이벤트 활성화하여 스레드가 실행되도록 설정

    def streaming_loop():
        while streaming_active:
            # Picamera2로부터 프레임을 읽음
            frame = picam2.capture_array()
            # YOLOv8 추론 실행
            results = model(frame)
            # 결과를 시각화하여 프레임에 표시
            annotated_frame = results[0].plot()
            # 객체 인식 결과를 CSV 파일에 기록
            process_result_and_update_csv(results, csv_file_path)
            # OpenCV로 감지된 프레임을 화면에 표시
            cv2.imshow("Camera", annotated_frame)
            # 'q' 키가 눌리면 스트리밍 종료
            if cv2.waitKey(1) == ord("q"):
                stop_streaming()
                break

    # 스트리밍 루프를 스레드로 시작
    threading.Thread(target=streaming_loop).start()

def stop_streaming():
    global streaming_active
    streaming_active = False
    streaming_event.clear()  # 이벤트 비활성화하여 스레드가 멈추도록 설정
    cv2.destroyAllWindows()

# 스트리밍 시작
start_streaming()

# 'q' 키를 누르면 스트리밍 중지
while True:
    key = cv2.waitKey(1)
    if key == ord('q'):
        stop_streaming()
        break
    elif key == ord('s'):  # 's' 키를 누르면 스트리밍 다시 시작
        if not streaming_active:
            start_streaming()
