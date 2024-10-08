from __future__ import annotations
from pathlib import Path
import numpy as np
from igor2 import binarywave
import matplotlib.pyplot as plt
from utils.constants import STANDARDISED_METADATA_DICT_KEYS

def _ibw_pixel_to_nm_scaling(scan: dict) -> float:
    """
    Extract pixel to nm scaling from the IBW image metadata.

    Parameters
    ----------
    scan : dict
        The loaded binary wave object.

    Returns
    -------
    float
        A value corresponding to the real length of a single pixel.
    """
    notes = {}
    for line in str(scan["wave"]["note"]).split("\\r"):
        if ":" in line:
            key, val = line.split(":", 1)
            notes[key.strip()] = val.strip()
    return (
        1/(float(notes["SlowScanSize"]) / scan["wave"]["wData"].shape[0] * 1e9),  # Convert to nm
        1/(float(notes["FastScanSize"]) / scan["wave"]["wData"].shape[1] * 1e9),  # Convert to nm
    )[0]

def extract_metadata(notes: str) -> dict:
    """
    Extract metadata from the IBW notes.

    Parameters
    ----------
    notes : str
        The notes string from the IBW file.

    Returns
    -------
    dict
        A dictionary containing extracted metadata.
    """
    metadata = {}
    for line in notes.split("\\r"):
        if ":" in line:
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip()
    return metadata

def open_ibw(file_path: Path | str, channel: str) -> tuple[np.ndarray, dict, list]:
    """
    Load image from Asylum Research (Igor) .ibw files.

    Parameters
    ----------
    file_path : Path | str
        Path to the .ibw file.
    channel : str
        The channel to extract from the .ibw file.

    Returns
    -------
    tuple[np.ndarray, dict, list]
        A tuple containing the image, metadata, and parameter values.

    Raises
    ------
    FileNotFoundError
        If the file is not found.
    ValueError
        If the channel is not found in the .ibw file.
    """
    file_path = Path(file_path)
    scan = binarywave.load(file_path)
    labels = []
    for label_list in scan["wave"]["labels"]:
        for label in label_list:
            if label:
                labels.append(label.decode())
    if channel not in labels:
        channel = labels[0]
    
    channel_idx = labels.index(channel)
    image = scan["wave"]["wData"][:, :, channel_idx].T * 1e9  # Convert to nm
    image = np.flipud(image)
    scaling = _ibw_pixel_to_nm_scaling(scan)
    metadata = extract_metadata(str(scan["wave"]["note"]))
    metadata['scaling_factor'] = scaling

    num_frames = 1  # IBW files are typically single frames
    x_range_nm = float(metadata.get("FastScanSize", "0")) * 1e9
    y_pixels = int(metadata.get("ScanLines", "0"))
    x_pixels = int(metadata.get("ScanPoints", "0"))
    scan_rate = float(metadata.get("ScanRate", "0"))

    
    line_rate = 1 / scan_rate if y_pixels else 0
    fps = 1/(y_pixels * scan_rate) if scan_rate != 0 else 0
    pixel_to_nanometre_scaling_factor = scaling

    values = [
        num_frames,
        x_range_nm,
        fps,
        line_rate,
        y_pixels,
        x_pixels,
        pixel_to_nanometre_scaling_factor,
        channel,
        None
    ]

    if len(values) != len(STANDARDISED_METADATA_DICT_KEYS):
        raise ValueError(f"The length of the values in .ibw does not match the required metadata keys.")

    # Create the metadata dictionary
    file_metadata = dict(zip(STANDARDISED_METADATA_DICT_KEYS, values))

    return image, file_metadata, labels

if __name__ == "__main__":
    file_path = 'data/tops70s14_190g0000.ibw'
    channel = 'HeightTracee'  # Replace with the appropriate channel name
    try:
        im, metadata = open_ibw(file_path, channel)
        print(f"Scaling factor: {metadata['scaling_factor']} nm/pixel")
        print(f"Image shape: {im.shape}")
        print("Metadata:", metadata)

        # Single frame case
        plt.imshow(im, cmap=AFM)
        plt.colorbar(label='Height (nm)')
        plt.show()

    except Exception as e:
        print(f"Error: {e}")
