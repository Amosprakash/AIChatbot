import cv2
import time
import numpy as np
from paddleocr import PaddleOCR


# Initialize OCR engines
paddle = PaddleOCR(use_angle_cls=True, lang='en')  # Can specify your custom model path


# Load your test image
img_path = "Input\computer.jpg"
img = cv2.imread(img_path)

# Optional: preprocess image
def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=30)
    # Adaptive threshold
    gray = cv2.adaptiveThreshold(gray, 255,
                                 cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 15)
    return gray

preprocessed_img = preprocess(img)

# --------------------------
# PaddleOCR
start = time.time()
paddle_results = paddle.ocr(preprocessed_img, cls=True)
paddle_time = time.time() - start

paddle_texts = []
for line in paddle_results[0]:
    text, conf = line[1]
    paddle_texts.append(f"{text} ({conf:.2f})")

print("=== PaddleOCR ===")
print("\n".join(paddle_texts))
print(f"Time: {paddle_time:.2f}s\n")

