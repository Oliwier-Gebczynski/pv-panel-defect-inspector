import subprocess
import json

def extract_metadata(file_path: str):
    terminal = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]

    try:
        result = subprocess.run(terminal, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        return metadata
    except subprocess.CalledProcessError as e:
        return {"error": f"Błąd podczas odczytu metadanych: {e}"}

if __name__ == "__main__":
    file_path = "../data/raw/thermal/frame_000000.tiff"
    data = extract_metadata(file_path)
    print(json.dumps(data, indent=4, ensure_ascii=False))