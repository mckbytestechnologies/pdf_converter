import matplotlib.pyplot as plt
import numpy as np

def calculate_postnet_checksum(zip_code):
    """Calculate POSTNET checksum digit"""
    total = sum(int(d) for d in zip_code)
    checksum = (10 - (total % 10)) % 10
    return checksum

def digit_to_postnet(digit):
    """Convert digit to POSTNET pattern (1=tall, 0=short)"""
    patterns = {
        '0': '11000',
        '1': '00011',
        '2': '00101',
        '3': '00110',
        '4': '01001',
        '5': '01010',
        '6': '01100',
        '7': '10001',
        '8': '10010',
        '9': '10100'
    }
    return patterns[digit]

def generate_postnet_barcode(zip_code, filename=None):
    zip_code = zip_code.replace('-', '')
    checksum = str(calculate_postnet_checksum(zip_code))
    full_code = zip_code + checksum

    barcode_pattern = ['1'] 
    
    for digit in full_code:
        barcode_pattern.extend(list(digit_to_postnet(digit)))
    
    barcode_pattern.append('1') 
    bar_height = [0.125 if bit == '1' else 0.05 for bit in barcode_pattern]
    bar_positions = np.arange(len(barcode_pattern))
    fig, ax = plt.subplots(figsize=(10, 2))
    ax.bar(bar_positions, bar_height, width=0.8, color='black')
    ax.axis('off')
    ax.set_ylim(0, 0.15)
    ax.set_xlim(-1, len(barcode_pattern))
    
    plt.subplots_adjust(left=0.05, right=0.95)
    
    if filename:
        plt.savefig(filename, bbox_inches='tight', pad_inches=0.1, dpi=300)
        print(f"Barcode saved as {filename}")
    else:
        plt.show()

generate_postnet_barcode("17055-904921", "postnet_barcode.png")


