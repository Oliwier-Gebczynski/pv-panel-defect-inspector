import argparse
import os
import cv2
from core.detection.defect_detector import ThermalDefectDetector
from core.reporting.pdf_report_generator import PDFReportGenerator
from core.video_processing.fps_reducer import FPSReducer
from core.video_processing.metadata_extractor import MetadataExtractor
from core.video_processing.video_synchronizer import VideoSynchronizer
from core.video_processing.thermal_rgb_aligner import ThermalRGBAligner


class DefectInspector:
    """Main class for the PV Panel Defect Inspector."""

    def __init__(self, args):
        """Initializes the DefectInspector.

        Args:
            args: Command-line arguments.
        """

        self.args = args
        os.makedirs(self.args.output_dir, exist_ok=True)

    def run(self):
        """Runs the appropriate command based on user input."""
        if self.args.command == "process":
            self.process()
        else:
            print(f"Unknown command: {self.args.command}")

    def process(self):
        """Processes media based on the specified mode."""

        mode = self.args.mode
        if mode == "video-rgb-thermal":
            self.process_video_rgb_thermal()
        elif mode == "video-thermal":
            self.process_video_thermal()
        elif mode == "photo-rgb-thermal":
            self.process_photo_rgb_thermal()
        elif mode == "photo-thermal":
            self.process_photo_thermal()
        else:
            print(f"Unknown mode for process command: {mode}")

    def process_video_rgb_thermal(self):
        """Processes RGB and Thermal videos to detect defects."""

        print("Processing RGB + Thermal Video...")
        rgb_metadata_path = os.path.join(self.args.output_dir, "rgb_metadata.json")
        thermal_metadata_path = os.path.join(self.args.output_dir, "thermal_metadata.json")
        MetadataExtractor(self.args.rgb_input, rgb_metadata_path).extract()
        MetadataExtractor(self.args.thermal_input, thermal_metadata_path).extract()

        reduced_rgb_path = os.path.join(self.args.output_dir, "5fps_rgb.mp4")
        reduced_thermal_path = os.path.join(self.args.output_dir, "5fps_thermal.mp4")
        FPSReducer(self.args.rgb_input, rgb_metadata_path).generate_5fps_video(reduced_rgb_path)
        FPSReducer(self.args.thermal_input, thermal_metadata_path, grayscale=True).generate_5fps_video(reduced_thermal_path)

        defect_output_dir = os.path.join(self.args.output_dir, "detection")
        detector = ThermalDefectDetector(
            panel_model_path="core/detection/models/panel_detector_gpu_thermal/weights/best.pt",
            panel_model_rgb_path="core/detection/models/panel_detector_gpu/weights/best.pt",
            defect_model_path="core/detection/models/panel_defect_thermal/weights/best.pt",
            calibration_path=self.args.calibration_file,
            output_dir=defect_output_dir
        )
        detector.process_video(reduced_thermal_path, reduced_rgb_path)

        aligner = ThermalRGBAligner()
        if not aligner.load_calibration_from_json(self.args.calibration_file):
            print("Calibration file not found. Please run 'python calibrate.py' to generate it.")
            return
        processed_thermal_path = os.path.join(defect_output_dir, "5fps_thermal_processed.mp4")
        synchronizer = VideoSynchronizer(reduced_rgb_path, processed_thermal_path)
        overlay_video_path = os.path.join(self.args.output_dir, "overlay.mp4")
        synchronizer.generate_overlay_video(aligner, overlay_video_path)

        report_path = os.path.join(self.args.output_dir, "report.pdf")
        reporter = PDFReportGenerator(os.path.join(defect_output_dir, "crops"), report_path)
        reporter.generate()
        print("Processing finished.")

    def process_video_thermal(self):
        """Processes a thermal video to detect defects."""

        print("Processing Thermal Video...")
        thermal_metadata_path = os.path.join(self.args.output_dir, "thermal_metadata.json")
        MetadataExtractor(self.args.thermal_input, thermal_metadata_path).extract()

        reduced_thermal_path = os.path.join(self.args.output_dir, "5fps_thermal.mp4")
        FPSReducer(self.args.thermal_input, thermal_metadata_path, grayscale=True).generate_5fps_video(reduced_thermal_path)

        defect_output_dir = os.path.join(self.args.output_dir, "detection")
        detector = ThermalDefectDetector(
            panel_model_path="core/detection/models/panel_detector_gpu_thermal/weights/best.pt",
            panel_model_rgb_path="core/detection/models/panel_detector_gpu/weights/best.pt",
            defect_model_path="core/detection/models/panel_defect_thermal/weights/best.pt",
            calibration_path=self.args.calibration_file,
            output_dir=defect_output_dir
        )
        detector.process_video(reduced_thermal_path)

        report_path = os.path.join(self.args.output_dir, "report.pdf")
        reporter = PDFReportGenerator(os.path.join(defect_output_dir, "crops"), report_path)
        reporter.generate()
        print("Processing finished.")

    def process_photo_rgb_thermal(self):
        """Processes RGB and thermal photos to detect defects."""

        print("Processing RGB + Thermal Photo...")
        defect_output_dir = os.path.join(self.args.output_dir, "detection")
        detector = ThermalDefectDetector(
            panel_model_path="core/detection/models/panel_detector_gpu_thermal/weights/best.pt",
            panel_model_rgb_path="core/detection/models/panel_detector_gpu/weights/best.pt",
            defect_model_path="core/detection/models/panel_defect_thermal/weights/best.pt",
            calibration_path=self.args.calibration_file,
            output_dir=defect_output_dir
        )
        detector.process_image(self.args.thermal_input)

        aligner = ThermalRGBAligner()
        if not aligner.load_calibration_from_json(self.args.calibration_file):
            print("Calibration file not found. Please run 'python calibrate.py' to generate it.")
            return
        synchronizer = VideoSynchronizer(self.args.rgb_input, self.args.thermal_input)
        overlay_image_path = os.path.join(self.args.output_dir, "overlay.jpg")
        synchronizer.generate_overlay_image(aligner, overlay_image_path)

        report_path = os.path.join(self.args.output_dir, "report.pdf")
        reporter = PDFReportGenerator(os.path.join(defect_output_dir, "crops"), report_path)
        reporter.generate()
        print("Processing finished.")

    def process_photo_thermal(self):
        """Processes a thermal photo to detect defects."""
        
        print("Processing Thermal Photo...")
        defect_output_dir = os.path.join(self.args.output_dir, "detection")
        detector = ThermalDefectDetector(
            panel_model_path="core/detection/models/panel_detector_gpu_thermal/weights/best.pt",
            panel_model_rgb_path="core/detection/models/panel_detector_gpu/weights/best.pt",
            defect_model_path="core/detection/models/panel_defect_thermal/weights/best.pt",
            calibration_path=self.args.calibration_file,
            output_dir=defect_output_dir
        )
        detector.process_image(self.args.thermal_input)

        report_path = os.path.join(self.args.output_dir, "report.pdf")
        reporter = PDFReportGenerator(os.path.join(defect_output_dir, "crops"), report_path)
        reporter.generate()
        print("Processing finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PV Panel Defect Inspector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_process = subparsers.add_parser("process", help="Process media to find defects.")
    parser_process.add_argument("--mode",
                                type=str,
                                required=True,
                                choices=["video-rgb-thermal",
                                         "video-thermal",
                                         "photo-rgb-thermal",
                                         "photo-thermal"],
                                help="Processing mode")
    parser_process.add_argument("--thermal-input", type=str, required=True, help="Path to the thermal input file (video or image).")
    parser_process.add_argument("--rgb-input", type=str, help="Path to the RGB input file (video or image).")
    parser_process.add_argument("--output-dir", type=str, default="results", help="Directory to save the results.")
    parser_process.add_argument("--calibration-file", type=str, default="calibration.json", help="Path to calibration file.")

    args = parser.parse_args()

    inspector = DefectInspector(args)
    inspector.run()
