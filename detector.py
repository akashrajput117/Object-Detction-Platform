import cv2
from ultralytics import YOLO
import logging
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cyberpunk 2077 HUD Palette (BGR format for OpenCV)
CYBER_YELLOW = (10, 238, 252)   # #FCEE0A
CYBER_CYAN = (255, 240, 0)      # #00F0FF
CYBER_RED = (60, 0, 255)        # #FF003C
CYBER_GREEN = (157, 255, 0)     # #00FF9D
CYBER_DARK = (8, 5, 5)          # Deep background

class ObjectDetector:
    def __init__(self, model_path="yolov8n.pt"):
        self.model_path = model_path
        self.model = None
        self.load_model()
        
    def load_model(self):
        """Load the YOLO model."""
        try:
            self.model = YOLO(self.model_path)
            logging.info(f"Successfully loaded YOLO model: {self.model_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to load YOLO model: {e}")
            self.model = None
            return False
            
    def is_model_loaded(self):
        return self.model is not None

    def process_frame(self, frame, conf_threshold=0.5, selected_classes=None):
        """
        Process a single frame with Cyberpunk 2077 Kiroshi Optics HUD targeting.
        Returns:
            processed_frame (numpy.ndarray): Frame with Cyberpunk HUD bounding boxes.
            detections (list): List of dictionaries containing detection info.
        """
        if not self.is_model_loaded() or frame is None:
            return frame, []
            
        annotated_frame = frame.copy()
        detections = []
        
        try:
            # Run inference
            results = self.model(annotated_frame, verbose=False)[0]
            
            for box in results.boxes:
                conf = float(box.conf[0])
                if conf < conf_threshold:
                    continue
                    
                cls_id = int(box.cls[0])
                class_name = self.model.names[cls_id]
                
                # Filter by class if selected_classes is provided
                if selected_classes and "All" not in selected_classes and class_name not in selected_classes:
                    continue
                    
                # Get bounding box coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                bbox_w = max(0, x2 - x1)
                bbox_h = max(0, y2 - y1)
                
                detections.append({
                    'class_name': class_name,
                    'confidence': conf,
                    'bbox_x': x1,
                    'bbox_y': y1,
                    'bbox_w': bbox_w,
                    'bbox_h': bbox_h
                })
                
                # Assign Cyberpunk color based on class
                if class_name in ["person"]:
                    color = CYBER_YELLOW
                elif class_name in ["car", "bus", "truck", "motorcycle", "bicycle"]:
                    color = CYBER_CYAN
                else:
                    color = CYBER_GREEN

                # Draw base bounding box (thin tech border)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 1)

                # Draw Cyberpunk HUD Corner Brackets (Kiroshi Optics target lock)
                corner_len = max(8, min(24, int(min(bbox_w, bbox_h) * 0.25)))
                bracket_thickness = 3
                
                # Top-Left Corner
                cv2.line(annotated_frame, (x1, y1), (x1 + corner_len, y1), color, bracket_thickness)
                cv2.line(annotated_frame, (x1, y1), (x1, y1 + corner_len), color, bracket_thickness)
                
                # Top-Right Corner
                cv2.line(annotated_frame, (x2, y1), (x2 - corner_len, y1), color, bracket_thickness)
                cv2.line(annotated_frame, (x2, y1), (x2, y1 + corner_len), color, bracket_thickness)
                
                # Bottom-Left Corner
                cv2.line(annotated_frame, (x1, y2), (x1 + corner_len, y2), color, bracket_thickness)
                cv2.line(annotated_frame, (x1, y2), (x1, y2 - corner_len), color, bracket_thickness)
                
                # Bottom-Right Corner
                cv2.line(annotated_frame, (x2, y2), (x2 - corner_len, y2), color, bracket_thickness)
                cv2.line(annotated_frame, (x2, y2), (x2, y2 - corner_len), color, bracket_thickness)

                # Tech label with Cyberpunk styling: [ CLASS // CONF% ]
                label = f"[{class_name.upper()} // {int(conf*100)}%]"
                font = cv2.FONT_HERSHEY_DUPLEX
                font_scale = 0.45
                thickness = 1
                (w, h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
                
                # Ensure label box stays inside image bounds
                label_y2 = y1 if y1 >= h + 8 else y1 + h + 10
                label_y1 = label_y2 - h - 8
                
                # Draw solid label background in dark with color outline
                cv2.rectangle(annotated_frame, (x1, label_y1), (x1 + w + 8, label_y2), CYBER_DARK, -1)
                cv2.rectangle(annotated_frame, (x1, label_y1), (x1 + w + 8, label_y2), color, 1)
                
                # Draw text in bright Cyberpunk color
                cv2.putText(annotated_frame, label, (x1 + 4, label_y2 - 5), font, font_scale, color, thickness, cv2.LINE_AA)
                
        except Exception as e:
            logging.error(f"Error during frame processing: {e}")
            
        return annotated_frame, detections
