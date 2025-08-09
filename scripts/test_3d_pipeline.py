#!/usr/bin/env python3
"""
Test script for 3D Structure Prediction Pipeline

This script helps validate the 3D structure prediction pipeline and identify common issues.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def check_prerequisites() -> Dict[str, bool]:
    """Check if all prerequisites are met."""
    results = {}
    
    print("🔍 Checking prerequisites...")
    
    # Check if we're on the remote server
    work_dir = Path("/orcd/data/mbathe/001/rcm095/RNA_predictions")
    results['remote_server'] = work_dir.exists()
    print(f"  {'✓' if results['remote_server'] else '✗'} Remote server access: {results['remote_server']}")
    
    # Check SLURM availability
    try:
        result = subprocess.run(["which", "sbatch"], capture_output=True, text=True)
        results['slurm_available'] = result.returncode == 0
        print(f"  {'✓' if results['slurm_available'] else '✗'} SLURM available: {results['slurm_available']}")
    except Exception:
        results['slurm_available'] = False
        print("  ✗ SLURM available: False")
    
    # Check conda environment
    try:
        result = subprocess.run(["conda", "info", "--envs"], capture_output=True, text=True)
        results['conda_available'] = result.returncode == 0
        print(f"  {'✓' if results['conda_available'] else '✗'} Conda available: {results['conda_available']}")
    except Exception:
        results['conda_available'] = False
        print("  ✗ Conda available: False")
    
    # Check 3D structure prediction tools
    tools = {
        'rosetta': 'rna_rosetta_run.py',
        'simrna': 'SimRNA',
        'farna': 'farna',
        'rna_composer': 'RNAComposer'
    }
    
    for tool_name, command in tools.items():
        try:
            result = subprocess.run(["which", command], capture_output=True, text=True)
            results[f'{tool_name}_available'] = result.returncode == 0
            print(f"  {'✓' if results[f'{tool_name}_available'] else '⚠️'} {tool_name.title()} available: {results[f'{tool_name}_available']}")
        except Exception:
            results[f'{tool_name}_available'] = False
            print(f"  ⚠️ {tool_name.title()} available: False")
    
    return results


def check_rnafold_results(sequence_prefix: str) -> Dict[str, bool]:
    """Check if RNAfold results exist for the given sequence."""
    results = {}
    
    print(f"\n🔍 Checking RNAfold results for {sequence_prefix}...")
    
    work_dir = Path("/orcd/data/mbathe/001/rcm095/RNA_predictions")
    sequence_name = f"{sequence_prefix}_5UTR"
    
    # Check comprehensive results with multiple possible names
    possible_comprehensive_files = [
        work_dir / "output" / "comparisons" / f"{sequence_name}_comprehensive_results.json",
        work_dir / "output" / "comparisons" / f"{sequence_prefix}_comprehensive_results.json",
        work_dir / "output" / "comparisons" / f"{sequence_prefix}_5UTR_comprehensive_results.json"
    ]
    
    comprehensive_file = None
    for file_path in possible_comprehensive_files:
        if file_path.exists():
            comprehensive_file = file_path
            break
    
    results['comprehensive_results'] = comprehensive_file is not None
    if comprehensive_file:
        print(f"  ✓ Comprehensive results: {comprehensive_file}")
    else:
        print(f"  ✗ Comprehensive results: Not found")
        print(f"    Checked for: {[str(f) for f in possible_comprehensive_files]}")
    
    # Check individual method results
    rnafold_dir = work_dir / "output" / "sequences" / sequence_name / "rnafold"
    if rnafold_dir.exists():
        method_dirs = [d for d in rnafold_dir.iterdir() if d.is_dir()]
        results['individual_results'] = len(method_dirs) > 0
        print(f"  {'✓' if results['individual_results'] else '✗'} Individual results: {len(method_dirs)} methods found")
        
        for method_dir in method_dirs:
            method_name = method_dir.name
            parsed_file = method_dir / "parsed_results" / "structure_parsed.json"
            if parsed_file.exists():
                print(f"    ✓ {method_name}: {parsed_file}")
            else:
                print(f"    ✗ {method_name}: No parsed results")
    else:
        results['individual_results'] = False
        print(f"  ✗ Individual results: {rnafold_dir} not found")
    
    return results


def check_3d_structure_directories(sequence_prefix: str) -> Dict[str, bool]:
    """Check if 3D structure directories exist and are properly set up."""
    results = {}
    
    print(f"\n🔍 Checking 3D structure directories for {sequence_prefix}...")
    
    work_dir = Path("/orcd/data/mbathe/001/rcm095/RNA_predictions")
    sequence_name = f"{sequence_prefix}_5UTR"
    structure_3d_dir = work_dir / "output" / "3d_structures" / sequence_name
    
    results['base_directory'] = structure_3d_dir.exists()
    print(f"  {'✓' if results['base_directory'] else '✗'} Base directory: {structure_3d_dir}")
    
    if structure_3d_dir.exists():
        # Check method directories
        methods = ['rosetta', 'simrna', 'farna', 'rna_composer']
        for method in methods:
            method_dir = structure_3d_dir / method
            if method_dir.exists():
                subdirs = ['input', 'output', 'logs', 'quality', 'slurm_scripts']
                missing_subdirs = []
                for subdir in subdirs:
                    if not (method_dir / subdir).exists():
                        missing_subdirs.append(subdir)
                
                if missing_subdirs:
                    print(f"    ⚠️ {method}: Missing subdirectories: {', '.join(missing_subdirs)}")
                    results[f'{method}_complete'] = False
                else:
                    print(f"    ✓ {method}: All subdirectories present")
                    results[f'{method}_complete'] = True
            else:
                print(f"    ✗ {method}: Directory not found")
                results[f'{method}_complete'] = False
    else:
        for method in ['rosetta', 'simrna', 'farna', 'rna_composer']:
            results[f'{method}_complete'] = False
    
    return results


def test_3d_pipeline(sequence_prefix: str, methods: List[str] = None) -> bool:
    """Test the 3D structure prediction pipeline."""
    print(f"\n🧪 Testing 3D structure prediction pipeline for {sequence_prefix}...")
    
    if methods is None:
        methods = ['rosetta']
    
    # Import the pipeline
    try:
        sys.path.append(str(Path(__file__).parent))
        from mrna_3d_structure_pipeline import mRNA3DStructurePipeline
    except ImportError as e:
        print(f"✗ Failed to import 3D structure pipeline: {e}")
        return False
    
    try:
        # Create pipeline instance
        pipeline = mRNA3DStructurePipeline(sequence_prefix)
        
        # Setup directories
        pipeline.setup_directories()
        print("✓ Directories set up successfully")
        
        # Load RNAfold results
        rnafold_results = pipeline.load_rnafold_results()
        if not rnafold_results:
            print("✗ No RNAfold results found")
            return False
        
        print(f"✓ Loaded {len(rnafold_results)} RNAfold results")
        
        # Test with first method only
        test_method = methods[0] if methods else 'rosetta'
        print(f"Testing with {test_method}...")
        
        # Get first RNAfold result
        first_method = list(rnafold_results.keys())[0]
        rnafold_data = rnafold_results[first_method]
        
        sequence = rnafold_data.get('sequence', '')
        structure = rnafold_data.get('structure', '')
        
        if not sequence or not structure:
            print("✗ No sequence or structure found in RNAfold results")
            return False
        
        print(f"✓ Testing with sequence length: {len(sequence)} nt")
        
        # Test the prediction method
        if test_method in pipeline.available_3d_methods:
            # For rosetta, we need to pass output_dir
            if test_method == "rosetta":
                output_dir = pipeline.structure_3d_dir / test_method / "output" / first_method
                output_dir.mkdir(parents=True, exist_ok=True)
                result = pipeline.available_3d_methods[test_method](sequence, structure, first_method, output_dir)
            else:
                result = pipeline.available_3d_methods[test_method](sequence, structure, first_method)
            if result:
                print(f"✓ {test_method} prediction completed successfully")
                print(f"  Output file: {result.pdb_file}")
                return True
            else:
                print(f"✗ {test_method} prediction failed")
                return False
        else:
            print(f"✗ Method {test_method} not available")
            return False
        
    except Exception as e:
        print(f"✗ Pipeline test failed: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test 3D Structure Prediction Pipeline")
    parser.add_argument("sequence_prefix", help="Sequence prefix (e.g., TETRAHYMENA)")
    parser.add_argument("--methods", nargs="+", 
                       choices=["rosetta", "simrna", "farna", "rna_composer"],
                       default=["rosetta"],
                       help="3D structure prediction methods to test")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check prerequisites and existing results")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("3D Structure Prediction Pipeline Test")
    print("=" * 60)
    
    # Check prerequisites
    prerequisites = check_prerequisites()
    
    # Check RNAfold results
    rnafold_results = check_rnafold_results(args.sequence_prefix)
    
    # Check 3D structure directories
    structure_dirs = check_3d_structure_directories(args.sequence_prefix)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_good = True
    
    # Prerequisites
    print("Prerequisites:")
    for key, value in prerequisites.items():
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {value}")
        if not value and key in ['remote_server', 'slurm_available']:
            all_good = False
    
    # RNAfold results
    print("\nRNAfold Results:")
    for key, value in rnafold_results.items():
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {value}")
        if not value:
            all_good = False
    
    # 3D structure directories
    print("\n3D Structure Directories:")
    for key, value in structure_dirs.items():
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {value}")
        if not value and key in ['base_directory']:
            all_good = False
    
    if args.check_only:
        if all_good:
            print("\n🎉 All checks passed! Ready to run 3D structure predictions.")
        else:
            print("\n⚠️ Some checks failed. Please address the issues above before running 3D predictions.")
        return
    
    # Run actual test
    if all_good:
        print("\n🧪 Running pipeline test...")
        success = test_3d_pipeline(args.sequence_prefix, args.methods)
        
        if success:
            print("\n🎉 Pipeline test completed successfully!")
        else:
            print("\n⚠️ Pipeline test failed. Check the logs for details.")
    else:
        print("\n⚠️ Skipping pipeline test due to failed prerequisites.")


if __name__ == "__main__":
    main()
