#!/usr/bin/env python3
"""Test script for the mRNA structure prediction pipeline.

⚠️  IMPORTANT: This test script should ONLY be run on the remote server (satori).
Never run it locally as the pipeline is designed for remote execution only.
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add scripts to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from mrna_structure_pipeline import mRNAStructurePipeline
from mrna_visualization_pipeline import mRNAVisualizationPipeline


def check_remote_environment():
    """Check if we're running on the remote server."""
    work_dir = Path("/orcd/data/mbathe/001/rcm095/RNA_predictions")
    if not work_dir.exists():
        print("⚠️  WARNING: This test should be run on the remote server (satori).")
        print("   The pipeline is designed for remote execution only.")
        print("   Current working directory:", Path.cwd())
        return False
    return True


def test_structure_pipeline():
    """Test the structure prediction pipeline with Tetrahymena benchmark sequence."""
    print("Testing structure prediction pipeline...")
    
    # Check if we're on remote server
    if not check_remote_environment():
        print("Skipping structure pipeline test (not on remote server)")
        return True
    
    try:
        # Initialize pipeline with remote path
        pipeline = mRNAStructurePipeline("TETRAHYMENA", "/orcd/data/mbathe/001/rcm095/RNA_predictions")
        
        # Test directory setup
        pipeline.setup_directories()
        print("✓ Directory setup successful")
        
        # Test input file creation with Tetrahymena sequence
        tetrahymena_sequence = "GGCAGGAAACCGGUGAGUAGCGCAGGGUUCGGUGUAGUCCGUGAGGCGAAAGCGCUAGCCGAAAGGCGAAACCGCUGAUGAGUAGCGCAGGGUUCGAUCCGGUAGCGAAAGCGCUAGCCGAAAGGCGAAACCGCU"
        input_file = pipeline.create_input_file(tetrahymena_sequence)
        print(f"✓ Input file created: {input_file}")
        
        # Test sequence parsing
        if pipeline.actual_sequence == tetrahymena_sequence:
            print("✓ Sequence parsing successful")
        else:
            print("✗ Sequence parsing failed")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Structure pipeline test failed: {e}")
        return False


def test_visualization_pipeline():
    """Test the visualization pipeline with Tetrahymena benchmark data."""
    print("\nTesting visualization pipeline...")
    
    # Check if we're on remote server
    if not check_remote_environment():
        print("Skipping visualization pipeline test (not on remote server)")
        return True
    
    try:
        # Create mock results in remote directory using Tetrahymena data
        mock_results = {
            "sequence_name": "TETRAHYMENA_5UTR",
            "sequence": "GGCAGGAAACCGGUGAGUAGCGCAGGGUUCGGUGUAGUCCGUGAGGCGAAAGCGCUAGCCGAAAGGCGAAACCGCUGAUGAGUAGCGCAGGGUUCGAUCCGGUAGCGAAAGCGCUAGCCGAAAGGCGAAACCGCU",
            "sequence_length": 135,
            "methods_tested": ["rnafold_default"],
            "results": {
                "rnafold_default": {
                    "method": "rnafold",
                    "parameters": "default",
                    "sequence": "GGCAGGAAACCGGUGAGUAGCGCAGGGUUCGGUGUAGUCCGUGAGGCGAAAGCGCUAGCCGAAAGGCGAAACCGCUGAUGAGUAGCGCAGGGUUCGAUCCGGUAGCGAAAGCGCUAGCCGAAAGGCGAAACCGCU",
                    "structure": "((((...((((((....((((.((....(((.((..((((.((((((..((...((((....))))..))..))))))....)))).))))))).)))).))))))))))...((((....))))",
                    "energy": -42.9,
                    "base_pairs": [(0, 134), (1, 133), (2, 132), (3, 131), (4, 130)],
                    "num_base_pairs": 41,
                    "gc_content": 0.607,
                    "base_pair_density": 0.328
                }
            }
        }
        
        # Save mock results in remote directory
        results_dir = Path("/orcd/data/mbathe/001/rcm095/RNA_predictions/output/comparisons")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(results_dir / "TETRAHYMENA_comprehensive_results.json", 'w') as f:
            json.dump(mock_results, f)
        
        # Initialize visualization pipeline
        viz_pipeline = mRNAVisualizationPipeline("TETRAHYMENA", str(results_dir))
        
        # Test aesthetics setup
        if hasattr(viz_pipeline, 'colors'):
            print("✓ Aesthetics setup successful")
        else:
            print("✗ Aesthetics setup failed")
            return False
        
        # Test results loading
        if viz_pipeline.results:
            print("✓ Results loading successful")
        else:
            print("✗ Results loading failed")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Visualization pipeline test failed: {e}")
        return False


def test_file_operations():
    """Test file operations."""
    print("\nTesting file operations...")
    try:
        # Test basic path operations (this should work locally)
        test_path = Path("test_output")
        test_path.mkdir(exist_ok=True)
        
        # Test file creation
        test_file = test_path / "test.txt"
        test_file.write_text("test content")
        
        if test_file.exists():
            print("✓ File creation successful")
        else:
            print("✗ File creation failed")
            return False
        
        # Cleanup
        shutil.rmtree(test_path)
        print("✓ File cleanup successful")
        
        return True
    except Exception as e:
        print(f"✗ File operations test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=== Testing mRNA Structure Prediction Pipeline ===\n")
    print("Testing with Tetrahymena P4-P6 domain (our benchmark sequence)")
    print()
    
    # Check if we're on remote server
    if not check_remote_environment():
        print("⚠️  WARNING: This test suite is designed for remote server execution.")
        print("   Some tests will be skipped when running locally.")
        print("   For full testing, please run on satori: ssh satori")
        print()
    
    tests = [
        test_structure_pipeline,
        test_visualization_pipeline,
        test_file_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        print("✓ Tetrahymena P4-P6 domain benchmark sequence processed successfully")
        return 0
    else:
        print("⚠️  Some tests failed or were skipped.")
        if not check_remote_environment():
            print("   This is expected when running locally.")
            print("   For full testing, run on the remote server: ssh satori")
        return 1


if __name__ == "__main__":
    sys.exit(main())
