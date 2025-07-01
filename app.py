import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
import cvzone
from tracker import Tracker
import time

# Load YOLOv8 trained model
model = YOLO(r"model_training\best.pt")

# Read class names
with open("coco1.txt", "r") as f:
    class_list = f.read().splitlines()

# Optional: Mouse move coordinate display
def RGB(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        print([x, y])

cv2.namedWindow('RGB')
cv2.setMouseCallback('RGB', RGB)

# Load video
cap = cv2.VideoCapture(r'input_video\dronetreecount.mp4')

# Get video info for output
width = 1020
height = 600
fps_output = 30  # You can adjust this if needed

# Define video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output_video.mp4', fourcc, fps_output, (width, height))

# Initialize tracker and variables
tracker = Tracker()
cy1 = 485
offset = 10
plantcount = []
prev_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (width, height))

    # FPS Calculation
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time + 1e-6)
    prev_time = curr_time

    # YOLOv8 Inference
    results = model(frame)
    a = results[0].boxes.data

    if len(a) != 0:
        px = pd.DataFrame(a.cpu().numpy()).astype("float")
        detections = []

        for index, row in px.iterrows():
            x1 = int(row[0])
            y1 = int(row[1])
            x2 = int(row[2])
            y2 = int(row[3])
            class_id = int(row[5])
            if class_id < len(class_list):
                detections.append([x1, y1, x2, y2])

        bbox_idx = tracker.update(detections)

        for bbox in bbox_idx:
            x3, y3, x4, y4, id = bbox
            cx = (x3 + x4) // 2
            cy = (y3 + y4) // 2

            cv2.circle(frame, (cx, cy), 5, (255, 123, 23), -1)
            cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 255, 0), 2)
            cvzone.putTextRect(frame, f'ID: {id}', (x3, y3 - 10), 1, 1, colorR=(255, 255, 255), colorT=(0, 0, 0))

            if cy1 - offset < cy < cy1 + offset:
                cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 0, 255), 2)
                if id not in plantcount:
                    plantcount.append(id)

    # Counting line
    cv2.line(frame, (2, cy1), (1018, cy1), (255, 255, 255), 2)

    # Overlay (white background, black text)
    cvzone.putTextRect(frame, f'FPS: {int(fps)}', (50, 30), 2, 2, colorR=(255, 255, 255), colorT=(0, 0, 0))
    cvzone.putTextRect(frame, f'Plants Counted: {len(plantcount)}', (50, 70), 2, 2, colorR=(255, 255, 255), colorT=(0, 0, 0))

    # Show and save
    cv2.imshow("RGB", frame)
    out.write(frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()
