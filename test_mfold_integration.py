#!/usr/bin/env python3
"""
Test script to compare RNAfold and Mfold predictions on the same sequence.
"""

import subprocess
import tempfile
from pathlib import Path
import os

def test_rnafold(sequence, output_dir):
    """Test RNAfold prediction."""
    print("Testing RNAfold...")
    
    # Create input file
    input_file = output_dir / "test_sequence.fasta"
    with open(input_file, 'w') as f:
        f.write(f">test_sequence\n{sequence}\n")
    
    # Run RNAfold
    try:
        result = subprocess.run(['RNAfold', str(input_file)], 
                              capture_output=True, text=True, check=True,
                              cwd=output_dir)
        
        print("✓ RNAfold completed successfully")
        print(f"Output: {result.stdout}")
        
        # Save output
        with open(output_dir / "rnafold_output.txt", 'w') as f:
            f.write(result.stdout)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ RNAfold failed: {e}")
        print(f"Stderr: {e.stderr}")
        return False

def test_mfold(sequence, output_dir):
    """Test Mfold prediction."""
    print("Testing Mfold...")
    
    # Create input file
    input_file = output_dir / "test_sequence.fasta"
    with open(input_file, 'w') as f:
        f.write(f">test_sequence\n{sequence}\n")
    
    # Set environment variables for mfold
    env = os.environ.copy()
    env['SEQ'] = str(input_file)
    env['T'] = '37.0'
    env['MAX'] = '10'
    
    try:
        result = subprocess.run(['mfold'], 
                              capture_output=True, text=True, check=True,
                              cwd=output_dir, env=env)
        
        print("✓ Mfold completed successfully")
        print(f"Output: {result.stdout}")
        
        # Save output
        with open(output_dir / "mfold_output.txt", 'w') as f:
            f.write(result.stdout)
        
        # List created files
        print("Files created by Mfold:")
        for file in output_dir.glob("*"):
            print(f"  {file.name}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Mfold failed: {e}")
        print(f"Stderr: {e.stderr}")
        return False

def main():
    """Main test function."""
    # Test sequence (the same one we used before)
    test_sequence = "GGCAGGAAACCGGUGAGUAGCGCAGGGUUCGGUGUAGUCCGUGAGGCGAA"
    
    print(f"Testing sequence: {test_sequence}")
    print(f"Length: {len(test_sequence)} nucleotides")
    print("=" * 60)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"Using temporary directory: {temp_path}")
        
        # Test RNAfold
        print("\n" + "=" * 30)
        rnafold_success = test_rnafold(test_sequence, temp_path)
        
        # Test Mfold
        print("\n" + "=" * 30)
        mfold_success = test_mfold(test_sequence, temp_path)
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY:")
        print(f"RNAfold: {'✓ PASSED' if rnafold_success else '✗ FAILED'}")
        print(f"Mfold:   {'✓ PASSED' if mfold_success else '✗ FAILED'}")
        
        if rnafold_success and mfold_success:
            print("\nBoth tools are working! Ready for pipeline integration.")
        else:
            print("\nSome tools failed. Check the output above for details.")

if __name__ == "__main__":
    main()
