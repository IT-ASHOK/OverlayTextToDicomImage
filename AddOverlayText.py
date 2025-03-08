import time
import os
import numpy as np
import pydicom
from pydicom.dataset import Dataset
from PIL import Image, ImageDraw, ImageFont
from colorama import init, Back, Fore, Style

def add_dicom_overlay(dicom_file_path, text):
    font_size=40
    data_set = pydicom.dcmread(dicom_file_path)

    rows, cols = data_set.Rows, data_set.Columns
    # Create blank overlay (all zeros)
    overlay_data = np.zeros((rows, cols), dtype=np.uint8)

    # Convert overlay to PIL image for text drawing
    overlay_image = Image.fromarray(overlay_data, mode="L")  # Grayscale mode
    draw = ImageDraw.Draw(overlay_image)
        
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
    packed_overlay_data = np.packbits(overlay_data, axis=-1,bitorder="little").flatten() # Little-endian LSB 

    add_overlay_to_data_set(data_set,rows,cols,text,packed_overlay_data)
    save_modified_data_set(data_set, dicom_file_path)

def add_overlay_to_data_set(data_set, rows, cols, text, packed_overlay_data):
    try:
        overlay_group = 0x6000  # DICOM 6000 groups
    
        data_set[overlay_group, 0x0010] = pydicom.DataElement((overlay_group, 0x0010), "US", rows)   # Overlay Rows
        data_set[overlay_group, 0x0011] = pydicom.DataElement((overlay_group, 0x0011), "US", cols)   # Overlay Columns
        data_set[overlay_group, 0x0012] = pydicom.DataElement((overlay_group, 0x0012), "US", 1)      # Overlay Planes
        data_set[overlay_group, 0x0040] = pydicom.DataElement((overlay_group, 0x0040), "CS", "G")    # Overlay Type (Graphics)
        data_set[overlay_group, 0x0015] = pydicom.DataElement((overlay_group, 0x0015), "IS", "1")    # Number of Frames in Overlay
        data_set[overlay_group, 0x0050] = pydicom.DataElement((overlay_group, 0x0050), "SS", [1, 1]) # Overlay Origin
        data_set[overlay_group, 0x0100] = pydicom.DataElement((overlay_group, 0x0100), "US", 1)      # Overlay Bits Allocated
        data_set[overlay_group, 0x0102] = pydicom.DataElement((overlay_group, 0x0102), "US", 0)      # Overlay Bit Position
        data_set[overlay_group, 0x1500] = pydicom.DataElement((overlay_group, 0x1500), "LO", text)   # Overlay Label
        data_set[overlay_group, 0x3000] = pydicom.DataElement((overlay_group, 0x3000), "OB", packed_overlay_data.tobytes())  # Overlay Data

    except Exception as e:
        print_message_to_console(f"Error while adding overlay {e}", Fore.RED)

def save_modified_data_set(data_set, dicom_file_path):
    try:
        data_set.save_as(dicom_file_path)
    except Exception as e:
        print_message_to_console(f"Error while saving modified DICOM file {e}", Fore.RED)

def process_dicom_folder(folder_path, text):
    if not os.path.exists(folder_path):
        print_message_to_console("Folder does not exist.", Fore.RED)
        exit_program()

    dicom_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".dcm", ".ima"))]
    if len(dicom_files) == 0:
        print_message_to_console("No DICOM files found in the folder.", Fore.RED)
        exit_program()
    else:
        print_message_to_console(f"Processing {len(dicom_files)} DICOM files in '{folder_path}'...", Fore.BLUE)

    for dicom_file in dicom_files:
        dicom_path = os.path.join(folder_path, dicom_file)
        add_dicom_overlay(dicom_path, text)
                
    print_message_to_console("Added overlay text successfully!",Fore.GREEN)
    exit_program()

def print_message_to_console(message, color_code):
    print(f"\n{color_code}{message}{Style.RESET_ALL}") 
    
def exit_program():
    input("Press enter to exit...")
    os._exit(0)

if __name__ == "__main__": 
    print(Fore.YELLOW)
    input_folder = input("Please enter the DICOM files path: ").strip()
    overlay_text = input("Please enter the text to overlay: ").strip()
    
    process_dicom_folder(input_folder, overlay_text)
