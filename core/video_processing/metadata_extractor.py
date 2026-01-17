import subprocess
import json


class MetadataExtractor:
    """A class to extract frame metadata from a video file using ffprobe.
    
    This class extracts information about each frame in a video, such as its
    timestamp and frame type (I, P, B), and saves it to a JSON file.
    """

    def __init__(self, input_path: str, output_path: str):
        """Initializes the MetadataExtractor.

        Args:
            input_path: The path to the input video file.
            output_path: The path to save the extracted metadata in JSON format.
        """

        self.input_path = input_path
        self.output_path = output_path

    def _extract_video_data(self):
        """Extracts video metadata using ffprobe.

        Returns:
            A dictionary containing the extracted metadata, or an error
            dictionary if extraction fails.
        """

        terminal = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-select_streams", "v:0",
            "-show_entries",
            "stream=start_time,r_frame_rate,avg_frame_rate,duration",
            "-show_entries",
            "frame=pkt_pts_time,pkt_dts_time,pict_type",
            self.input_path
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

    def _format_frame_data(self, data):
        """Formats the extracted frame data.

        This method processes the raw metadata to create a list of dictionaries,
        each representing a frame with its ID, timestamp, and type.

        Args:
            data: The raw metadata extracted by ffprobe.

        Returns:
            A dictionary containing the formatted frame data.
        """

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

    def extract(self):
        """Extracts and saves the frame metadata.
        
        This method orchestrates the extraction and formatting of frame metadata
        and saves the result to the specified output file.
        """
        
        print(f"\nProcessing video: {self.input_path}")
        data = self._extract_video_data()

        if "error" in data:
            print(json.dumps(data, indent=4, ensure_ascii=False))
            return

        processed_data = self._format_frame_data(data)

        if "frames" in processed_data and "streams" in processed_data:
            try:
                with open(self.output_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_data['frames'], f, indent=4, ensure_ascii=False)
                print(f"Successfully saved frame data to: {self.output_path}")

            except IOError as e:
                print(f"Error: Could not write frame data to file {self.output_path}. Details: {e}")
        else:
            print(f"Error: 'frames' or 'streams' keys not found in ffprobe output.")
            print(f"Make sure the path leads to a correct VIDEO file.")
            print("Received data (or error):")
            print(json.dumps(processed_data, indent=4, ensure_ascii=False))
