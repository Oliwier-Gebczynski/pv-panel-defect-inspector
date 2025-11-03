import subprocess
import json
import sys
import os

def extract_video_data(file_path: str):
    terminal = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-select_streams", "v:0",
        "-show_entries",
        "stream=start_time,r_frame_rate,avg_frame_rate,duration",
        "-show_entries",
        "frame=pkt_pts_time,pkt_dts_time,pict_type",
        file_path
    ]

    print(f"Running command: {' '.join(terminal)}")

    try:
        result = subprocess.run(terminal, capture_output=True, text=True, check=True, timeout=300)
        metadata = json.loads(result.stdout)
        return metadata
    except subprocess.CalledProcessError as e:
        return {"error": f"Error reading metadata: {e}", "stderr": e.stderr}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout expired during file analysis."}

def format_frame_data(data):
    if "frames" not in data or "streams" not in data:
        return data

    fps = 0.0
    try:
        avg_frame_rate_str = data['streams'][0].get('avg_frame_rate')
        if avg_frame_rate_str and '/' in avg_frame_rate_str:
            num, den = avg_frame_rate_str.split('/')
            if float(den) != 0:
                fps = float(num) / float(den)
                print(f"Read FPS: {fps}")
            else:
                print("Error: FPS denominator is zero.")
        else:
            print(f"Warning: 'avg_frame_rate' in 'numerator/denominator' format not found.")
    except Exception as e:
        print(f"Warning: Failed to read avg_frame_rate. Fallback calculation may not work. Error: {e}")

    formatted_frames = []

    for index, frame in enumerate(data['frames']):
        timestamp = None

        timestamp_str = frame.get("pkt_pts_time")

        if timestamp_str is None:
            timestamp_str = frame.get("pkt_dts_time")

        if timestamp_str is not None:
            try:
                timestamp = float(timestamp_str)
            except ValueError:
                timestamp = None

        if timestamp is None and fps > 0:
            calculated_time = (index / fps)
            timestamp = calculated_time

        frame_data = {
            "id": index + 1,
            "time": timestamp,
            "type": frame.get("pict_type")
        }
        formatted_frames.append(frame_data)

    data['frames'] = formatted_frames
    return data

if __name__ == "__main__":
    file_path = "../data/processed/rgb_video.mp4"
    output_file_path = "../data/metadata/rgb_frames.json"

    data = extract_video_data(file_path)

    if "error" in data:
        print(json.dumps(data, indent=4, ensure_ascii=False))
        sys.exit(1)

    processed_data = format_frame_data(data)

    if "frames" in processed_data and "streams" in processed_data:
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data['frames'], f, indent=4, ensure_ascii=False)
            print(f"\nSuccessfully saved frame data to: {output_file_path}")

        except IOError as e:
            print(f"\nError: Could not write to file {output_file_path}. Details: {e}")
            sys.exit(1)
    else:
        print("Error: 'frames' or 'streams' keys not found in ffprobe output.")
        print("Make sure the path leads to a correct VIDEO file.")
        print("Received data (or error):")
        print(json.dumps(processed_data, indent=4, ensure_ascii=False))