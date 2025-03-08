import time
import os
import numpy as np
import pydicom
from pydicom.dataset import Dataset
from PIL import Image, ImageDraw, ImageFont

def add_dicom_overlay(dicom_file_path, text):
    ds = pydicom.dcmread(dicom_file_path)

    # DICOM 6000 groups
    overlay_group = 0x6000  

    rows, cols = ds.Rows, ds.Columns

    # Create blank overlay (all zeros)
    overlay_data = np.zeros((rows, cols), dtype=np.uint8)

    # Convert overlay to PIL image for text drawing
    overlay_image = Image.fromarray(overlay_data, mode="L")  # Grayscale mode
    draw = ImageDraw.Draw(overlay_image)
        
    font_size=40
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    
    # Get text size
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top

    # Position text in the center of the image
    position = ((cols - text_width) // 2, (rows - text_height) // 2)

    # Add text in white (1) to overlay image
    draw.text(position, text, fill=255, font=font)

    # Convert overlay to binary format (1-bit: 1 for text, 0 for background)
    overlay_data = np.array(overlay_image)
    overlay_data = (overlay_data > 0).astype(np.uint8)  # Convert grayscale to binary (0 or 1)

    # Pack overlay data into bytes (DICOM requires packed binary format)
    packed_overlay_data = np.packbits(overlay_data, axis=-1,bitorder="little").flatten()

    # Add overlay attributes to DICOM dataset
    ds[overlay_group, 0x0010] = pydicom.DataElement((overlay_group, 0x0010), "US", rows)   # Overlay Rows
    ds[overlay_group, 0x0011] = pydicom.DataElement((overlay_group, 0x0011), "US", cols)   # Overlay Columns
    ds[overlay_group, 0x0012] = pydicom.DataElement((overlay_group, 0x0012), "US", 1)      # Overlay Planes
    ds[overlay_group, 0x0040] = pydicom.DataElement((overlay_group, 0x0040), "CS", "G")    # Overlay Type (Graphics)
    ds[overlay_group, 0x0015] = pydicom.DataElement((overlay_group, 0x0015), "IS", "1")    # Number of Frames in Overlay
    ds[overlay_group, 0x0050] = pydicom.DataElement((overlay_group, 0x0050), "SS", [1, 1]) # Overlay Origin
    ds[overlay_group, 0x0100] = pydicom.DataElement((overlay_group, 0x0100), "US", 1)      # Overlay Bits Allocated
    ds[overlay_group, 0x0102] = pydicom.DataElement((overlay_group, 0x0102), "US", 0)      # Overlay Bit Position
    ds[overlay_group, 0x1500] = pydicom.DataElement((overlay_group, 0x1500), "LO", text) # Overlay Label
    ds[overlay_group, 0x3000] = pydicom.DataElement((overlay_group, 0x3000), "OB", packed_overlay_data.tobytes())  # Overlay Data

    # Save modified DICOM file
    ds.save_as(dicom_file_path)

def process_dicom_folder(folder_path, text):
    if not os.path.exists(folder_path):
        print("❌ Folder does not exist!")
        return

    dicom_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".dcm", ".ima"))]
    print(f"\n🔄 Processing {len(dicom_files)} DICOM files in '{folder_path}'...\n")

    for dicom_file in dicom_files:
        dicom_path = os.path.join(folder_path, dicom_file)
        add_dicom_overlay(dicom_path, text)

    print("\n✅ Added overlay text successfully!")
    time.sleep(5)

if __name__ == "__main__": 
    input_folder = input("📂 Enter the DICOM folder path: ").strip()
    overlay_text = input("📝 Enter the text to overlay: ").strip()
    
    process_dicom_folder(input_folder, overlay_text)
