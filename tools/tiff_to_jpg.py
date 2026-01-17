import cv2
import numpy as np
import os

def convert_tiff_to_grayscale_jpg(input_path, output_path):
    image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)

    if image is None:
        print(f"Błąd: Nie udało się otworzyć pliku {input_path}")
        return

    print(f"Oryginalny typ danych: {image.dtype}, Kształt: {image.shape}")

    if len(image.shape) == 3:
        print("Wykryto obraz kolorowy, konwertuję na szary...")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    normalized_image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
    
    final_image = normalized_image.astype(np.uint8)

    cv2.imwrite(output_path, final_image)
    print(f"Sukces! Zapisano plik: {output_path}")


input_file = "../data/raw/thermal/frame_000100.tiff"  
output_file = "../data/processed/thermal.jpg"

convert_tiff_to_grayscale_jpg(input_file, output_file)

