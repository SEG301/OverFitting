import sys
import os
from pathlib import Path

# Add project root to sys.path
root = str(Path(__file__).resolve().parent.parent.parent)
if root not in sys.path:
    sys.path.append(root)

# Ensure the script can find its stages
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import stages
import step1_mapping as stage1
import step2_deduplicate as stage2
import step3_cleaning as stage3
import step4_segmentation as stage4

def main_pipeline():
    print("=== OVERFITTING DATA PIPELINE ===")
    
    # Step 1: Mapping
    print("\nStep 1: Mapping Reviews to Enterprise Data...")
    stage1.run()
    
    # Step 2: Deduplicate
    print("\nStep 2: Deduplicating (Tax + Name + Address)...")
    stage2.run()
    
    # Step 3: Clean
    print("\nStep 3: Cleaning Data (Title Case, HTML Strip)...")
    stage3.run()
    
    # Step 4: Segment
    print("\nStep 4: Vietnamese Word Segmentation...")
    stage4.run()

    print("\nPIPELINE COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main_pipeline()
