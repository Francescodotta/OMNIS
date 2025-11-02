import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def check_pin_file(pin_file):
    """Basic checks for PIN file existence and format"""
    print("\n=== PIN File Basic Check ===")
    print(f"File path: {pin_file}")
    
    if not os.path.exists(pin_file):
        print("ERROR: PIN file not found!")
        return False
        
    try:
        with open(pin_file, 'r') as f:
            # Check header
            header = f.readline().strip().split('\t')
            if 'PSMId' not in header:
                print("ERROR: PIN file missing PSMId column!")
                return False
            
            print(f"\nHeader columns ({len(header)}):")
            for i, col in enumerate(header):
                print(f"{i}: {col}")
            
            return True
            
    except Exception as e:
        print(f"ERROR reading PIN file: {str(e)}")
        return False

def analyze_pin_file_details(pin_file):
    """Detailed analysis of PIN file PSM IDs and scan numbers"""
    print("\n=== Detailed PIN File Analysis ===")
    try:
        with open(pin_file, 'r') as f:
            header = f.readline().strip().split('\t')
            psm_id_idx = header.index('PSMId')
            
            # Analyze scan numbers
            scan_numbers = set()
            problematic_ids = []
            
            for line_num, line in enumerate(f, 1):
                fields = line.strip().split('\t')
                psm_id = fields[psm_id_idx]
                parts = psm_id.split('.')
                
                if len(parts) >= 3:
                    scan_num = parts[1]  # First scan number
                    scan_numbers.add(scan_num)
                    
                    # Check for potential issues
                    if len(parts) > 3:  # Has additional parts that might cause issues
                        problematic_ids.append((line_num, psm_id))
                        
            print(f"\nTotal unique scan numbers: {len(scan_numbers)}")
            print(f"Range: {min(scan_numbers)} to {max(scan_numbers)}")
            
            if problematic_ids:
                print("\nPotentially problematic PSM IDs:")
                for line_num, psm_id in problematic_ids[:5]:  # Show first 5 examples
                    print(f"Line {line_num}: {psm_id}")
                if len(problematic_ids) > 5:
                    print(f"...and {len(problematic_ids)-5} more")
                    
            return scan_numbers, problematic_ids
            
    except Exception as e:
        print(f"Error analyzing PIN file: {str(e)}")
        return None, None

def check_mzml_file(mzml_file):
    """Basic checks for mzML file existence and size"""
    print("\n=== mzML File Basic Check ===")
    print(f"File path: {mzml_file}")
    
    if not os.path.exists(mzml_file):
        print("ERROR: mzML file not found!")
        return False
        
    file_size = os.path.getsize(mzml_file)
    print(f"File size: {file_size / (1024*1024):.2f} MB")
    
    if file_size == 0:
        print("ERROR: mzML file is empty!")
        return False
        
    return True

def check_mzml_scan_numbers(mzml_file, pin_scan_numbers):
    """Check if mzML file contains the required scan numbers"""
    print("\n=== mzML Scan Number Verification ===")
    
    # This is a basic check - we'll look for some scan numbers in the file
    try:
        with open(mzml_file, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
            
            # Check first few scan numbers from PIN file
            test_scans = list(pin_scan_numbers)[:5]
            missing_scans = []
            
            for scan in test_scans:
                if f"scan={scan}" not in content:
                    missing_scans.append(scan)
                    
            if missing_scans:
                print("\nWarning: Some scan numbers from PIN file not found in mzML:")
                for scan in missing_scans:
                    print(f"- Scan {scan}")
            else:
                print("\nSample scan numbers verified in mzML file")
                
    except Exception as e:
        print(f"Error checking mzML file: {str(e)}")

def analyze_scan_psm_relationship(pin_file):
    """Analyze the relationship between scan numbers and PSM IDs"""
    print("\n=== Scan-PSM Relationship Analysis ===")
    try:
        with open(pin_file, 'r') as f:
            header = f.readline().strip().split('\t')
            psm_id_idx = header.index('PSMId')
            
            print("\nAnalyzing PSM ID structure:")
            print("Format should be: filename.scan.scan")
            print("\nExample PSM entries:")
            
            # Read and analyze first 5 lines
            for i in range(5):
                line = f.readline().strip()
                if not line:
                    break
                    
                fields = line.split('\t')
                psm_id = fields[psm_id_idx]
                parts = psm_id.split('.')
                
                print(f"\nPSM ID: {psm_id}")
                print(f"Number of parts: {len(parts)}")
                print("Parts breakdown:")
                for j, part in enumerate(parts):
                    print(f"  Part {j}: {part}")
                
                if len(parts) > 3:
                    print("  WARNING: Extra parts detected after scan number")
                
    except Exception as e:
        print(f"Error analyzing scan-PSM relationship: {str(e)}")

if __name__ == "__main__":
    # Use the same paths as before
    input_pin_file = os.path.join("/media/datastorage/it_cast/omnis_microservice_db/test_db/file_mzml/", 
                                 "percolator_results_psms.pin")
    mzml_file = os.path.join("/media/datastorage/it_cast/omnis_microservice_db/test_db/file_mzml", 
                            "20250228_04_01.mzML")
    
    # Run basic checks first
    pin_ok = check_pin_file(input_pin_file)
    mzml_ok = check_mzml_file(mzml_file)
    
    if pin_ok and mzml_ok:
        analyze_scan_psm_relationship(input_pin_file)
        # Run detailed analysis
        scan_numbers, problematic_ids = analyze_pin_file_details(input_pin_file)
        if scan_numbers:
            check_mzml_scan_numbers(mzml_file, scan_numbers)
            
        if problematic_ids:
            print("\nRecommendation:")
            print("The PSM IDs contain additional parts after the scan number")
            print("This might be causing the FlashLFQ error. Consider cleaning the PSM IDs")
            print("to match format: filename.scan.scan")
    else:
        print("\nFix basic file issues before detailed analysis.")
        sys.exit(1)