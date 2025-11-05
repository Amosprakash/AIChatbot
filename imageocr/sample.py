import cv2
import numpy as np
import os

# -----------------------------
# Helper Functions
# -----------------------------
def ensure(img):
    """Ensure image is BGR"""
    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif len(img.shape) == 3 and img.shape[2] == 3:
        return img
    elif len(img.shape) == 3 and img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    else: 
        raise ValueError(f"Unsupported image shape: {img.shape}")

def remove_background(img, debug=False):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    white_bg = np.ones_like(img, dtype=np.uint8) * 255
    white_bg[mask == 0] = img[mask == 0]
    if debug:
        cv2.imshow("White Background", white_bg)
        cv2.waitKey(0)
    return white_bg

def deblur(img, debug=False):
    blurred = cv2.GaussianBlur(img, (9, 9), 10)
    deblurred = cv2.addWeighted(img, 1.5, blurred, -0.5, 0)
    if debug:
        cv2.imshow("Deblurred", deblurred)
        cv2.waitKey(0)
    return deblurred

# -----------------------------
# Preprocessing Pipeline
# -----------------------------
def preprocess_image(img, debug=False):
    img = ensure(img)
    img = remove_background(img, debug=debug)
    img = deblur(img, debug=debug)

    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if debug: cv2.imshow("Grayscale", gray); cv2.waitKey(0)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=30)

    # Remove uneven lighting
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    norm = cv2.divide(gray, background, scale=255)
    if debug: cv2.imshow("Normalized", norm); cv2.waitKey(0)

    # Sharpen
    sharpen_kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])
    sharp = cv2.filter2D(norm, -1, sharpen_kernel)
    if debug: cv2.imshow("Sharpened", sharp); cv2.waitKey(0)

    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        sharp, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 15
    )

    # Optional invert if mostly dark text
    white_pixels = np.sum(thresh == 255)
    black_pixels = np.sum(thresh == 0)
    if black_pixels > white_pixels:
        thresh = cv2.bitwise_not(thresh)
    if debug: cv2.imshow("Thresholded", thresh); cv2.waitKey(0)

    if debug:
        cv2.destroyAllWindows()

    return thresh

def super_resolve(img,debug=False):
    try:
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel("FSRCNN_x4.pb")
        sr.setModel("fsrcnn", 4)
        img = sr.upsample(img)
        if debug:
             cv2.imshow("Super-resolution", img); cv2.waitKey(0)

        if debug:
            cv2.destroyAllWindows()
    except Exception as e:
        return(f"Super-resolution skipped: {e}")
    return img
# -----------------------------
# Main Function
# -----------------------------
def main():
    img_path = os.path.join("Input", "Sample.png")  # relative path
    if not os.path.exists(img_path):
        print("Image not found:", img_path)
        return

    img = cv2.imread(img_path)
    preprocessed = preprocess_image(img, debug=True)
    
    gray = super_resolve(preprocessed, debug=True)
    cv2.imwrite("super_resolve.png", gray)
    print("super_resolve done. Saved as super_resolve.png")

if __name__ == "__main__":
    main()
