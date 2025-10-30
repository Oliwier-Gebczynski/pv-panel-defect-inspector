import os
import unicodedata
import re

FOLDER_PATH = r"/home/opg/Documents/Github/pv-panel-defect-inspector/data/yolo/all_photos"

def normalize_filename(name: str) -> str:
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    return name

def rename_images(folder: str, prefix="panel"):
    files = sorted([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
    counter = 1

    for filename in files:
        old_path = os.path.join(folder, filename)
        name, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            print(f"Wrong file: {filename}")
            continue

        new_name = f"{prefix}_{counter:04d}{ext}"
        new_path = os.path.join(folder, new_name)

        os.rename(old_path, new_path)
        print(f"{filename} -> {new_name}")
        counter += 1

    print("\n Finished!")

if __name__ == "__main__":
    FOLDER_PATH = os.path.abspath(FOLDER_PATH)
    rename_images(FOLDER_PATH)
