import os
import shutil
import random
from pathlib import Path

base_path = Path("exports")
dataset_path = Path("dataset")

for split in ["train", "val", "test"]:
    (dataset_path / "images" / split).mkdir(parents=True, exist_ok=True)
    (dataset_path / "labels" / split).mkdir(parents=True, exist_ok=True)

images = list((base_path / "images").glob("*.jpg"))
random.shuffle(images)

n = len(images)
train_split = int(0.7 * n)
val_split = int(0.9 * n)

splits = {
    "train": images[:train_split],
    "val": images[train_split:val_split],
    "test": images[val_split:]
}

print(f"Found {n} images in total.")
print(f"  → train: {len(splits['train'])}")
print(f"  → val:   {len(splits['val'])}")
print(f"  → test:  {len(splits['test'])}")

for split, imgs in splits.items():
    for img_path in imgs:
        label_path = base_path / "labels" / f"{img_path.stem}.txt"
        target_img = dataset_path / "images" / split / img_path.name
        target_label = dataset_path / "labels" / split / f"{img_path.stem}.txt"

        shutil.copy(img_path, target_img)

        if label_path.exists():
            shutil.copy(label_path, target_label)
        else:
            target_label.touch()
            print(f"Warning: Missing label for {img_path.name}. Created an empty label file.")

print("\nDataset ready for YOLO training.")
