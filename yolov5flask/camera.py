
import cv2
from picamera2 import Picamera2
from ultralytics import YOLO

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

    def __del__(self):
        self.picam2.close()

    def get_frame(self):
        # Capture frame-by-frame
        frame = self.picam2.capture_array()
        if frame is None or frame.size == 0:
            print("Captured frame is empty")
            return None

        # Run YOLOv8 inference on the frame
        results = self.model(frame)

        # Visualize the results on the frame
        annotated_frame = results[0].plot()

        # Encode the frame to JPEG
        _, jpeg = cv2.imencode('.jpg', annotated_frame)
        return jpeg.tobytes()  # Return the byte data for the frame
