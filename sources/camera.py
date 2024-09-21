import cv2
import csv
import os
import time
from collections import defaultdict
from flask import Response
from picamera2 import Picamera2
from ultralytics import YOLO

#객체 인식, 프레임 리턴, csv 저장 통합

class VideoCamera:
    def __init__(self):
        # Initialize the Picamera2
        self.picam2 = Picamera2()
        self.picam2.preview_configuration.main.size = (1280, 720)
        self.picam2.preview_configuration.main.format = "RGB888"
        self.picam2.preview_configuration.align()
        self.picam2.configure("preview")
        self.picam2.start()

        # Load the YOLOv8 model
        self.model = YOLO("best (3).pt")

        # CSV file path
        self.csv_file_path = 'detections.csv'
        self.object_names = ['adult', 'kids']

    def __del__(self):
        self.picam2.close()

    def write_dict_to_csv(self, detections):
        """Write detections to CSV."""
        file_exists = os.path.isfile(self.csv_file_path)
        write_header = not file_exists or os.stat(self.csv_file_path).st_size == 0

        with open(self.csv_file_path, mode='a', newline='') as outfile:
            writer = csv.writer(outfile)
            if write_header:
                writer.writerow(['Name', 'Confidence'])

            for name, confidence in detections.items():
                if confidence <= 0.5:
                    confidence = 'N/A'
                writer.writerow([name, confidence])

    def process_result_and_update_csv(self, results):
        current_detections = defaultdict(float)

        for result in results:
            boxes = result.boxes
            if not boxes:
                continue

            for box in boxes:
                class_id = int(box.cls)
                name = self.object_names[class_id]
                confidence = float(box.conf)

                if confidence > 0.5:
                    current_detections[name] = max(current_detections.get(name, 0), confidence)

        self.write_dict_to_csv(current_detections)

    def get_frame(self):
        """Capture a frame from the camera, process it and return the annotated frame."""
        frame = self.picam2.capture_array()
        if frame is None or frame.size == 0:
            print("Captured frame is empty")
            return None

        # Run YOLOv8 inference on the frame
        results = self.model(frame)

        # Process results and update CSV
        self.process_result_and_update_csv(results)

        # Visualize the results on the frame
        annotated_frame = results[0].plot()

        # Encode the frame to JPEG
        _, jpeg = cv2.imencode('.jpg', annotated_frame)
        return jpeg.tobytes()  # Return the byte data for the frame

def startCAM():
    video_camera = VideoCamera()
    while True:
        frame = video_camera.get_frame()
        if frame is not None:
            yield frame

# Flask의 video_feed 엔드포인트와 연결할 수 있도록 설정합니다.
def video_feed():
    return Response(startCAM(), mimetype='multipart/x-mixed-replace; boundary=frame')
