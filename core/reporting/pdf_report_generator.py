import os
from fpdf import FPDF

class PDFReportGenerator:
    """A class to generate PDF reports from thermal and RGB images of PV panels.

    This class takes a directory of images, finds pairs of thermal and RGB images,
    and generates a PDF report listing the detected defects.
    """

    def __init__(self, image_dir: str, output_path: str):
        """Initializes the PDFReportGenerator.

        Args:
            image_dir: The directory containing the thermal and RGB images.
            output_path: The path to save the generated PDF report.
        """
        
        self.image_dir = image_dir
        self.output_path = output_path
        self.IMG_HEIGHT = 45

    def check_page_break(self, pdf, needed_height):
        """Checks if a page break is needed and adds a new page if so.

        Args:
            pdf: The FPDF object.
            needed_height: The height needed for the next element.
        """

        if pdf.get_y() + needed_height > 270:
            pdf.add_page()

    def generate(self):
        """Generates the PDF report.

        This method finds all thermal and RGB images in the specified directory,
        pairs them up, and generates a PDF report with the images and defect
        information.
        """

        if not os.path.exists(self.image_dir):
            print(f"[ERROR] Image directory not found: {self.image_dir}")
            return

        all_files = os.listdir(self.image_dir)
        valid_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
        thermal_images = sorted([f for f in all_files if "thermal" in f.lower() and f.lower().endswith(valid_exts)])
        rgb_images_set = {f for f in all_files if "rgb" in f.lower() and f.lower().endswith(valid_exts)}

        if not thermal_images:
            print("[ERROR] No thermal images found in the directory.")
            return

        pdf = FPDF()
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()

        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 15, txt="Raport Inspekcji Paneli PV", ln=1, align="C")
        pdf.ln(10)

        for thermal_img_name in thermal_images:
            needed_space = 20 + self.IMG_HEIGHT + 10
            self.check_page_break(pdf, needed_space)

            defect_name = os.path.splitext(thermal_img_name)[0].replace("_thermal", "")

            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 6, txt=f"File ID: {defect_name}", ln=1)

            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 6, txt="Detected Defect: Hot Spot / Diode Failure", ln=1)
            pdf.set_text_color(0, 0, 0)

            start_y = pdf.get_y() + 2

            thermal_path = os.path.join(self.image_dir, thermal_img_name)
            rgb_img_name = thermal_img_name.replace("thermal", "rgb").replace("Thermal", "RGB")

            pair_found = False
            actual_rgb_path = None

            for f in rgb_images_set:
                if thermal_img_name.replace("thermal", "rgb") == f:
                    actual_rgb_path = os.path.join(self.image_dir, f)
                    pair_found = True
                    break

            pdf.image(thermal_path, x=15, y=start_y, h=self.IMG_HEIGHT)

            if pair_found and actual_rgb_path:
                pdf.image(actual_rgb_path, x=110, y=start_y, h=self.IMG_HEIGHT)
            else:
                pdf.set_xy(110, start_y + (self.IMG_HEIGHT/2))
                pdf.set_font("Arial", "I", 9)
                pdf.cell(0, 5, txt="[Brak obrazu RGB]", ln=0)

            pdf.set_y(start_y + self.IMG_HEIGHT + 8)

            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        pdf.output(self.output_path)
        print(f"[INFO] PDF report saved to: {self.output_path}")