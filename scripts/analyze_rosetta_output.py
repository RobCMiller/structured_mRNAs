#!/usr/bin/env python3
"""
ROSETTA Silent File Analysis Script

This script analyzes ROSETTA 3D structure prediction output files (.out files)
and extracts comprehensive structural information including scores, base pairs,
and structural metrics.

Usage:
    python3 analyze_rosetta_output.py <silent_file.out>

Author: Generated for RNA Structure Prediction Pipeline
Date: August 2025
"""

import sys
import re
import os
from collections import defaultdict

def parse_rosetta_silent_file(filename):
    """
    Parse ROSETTA silent file and extract all structural information.
    
    Args:
        filename (str): Path to ROSETTA silent file (.out)
    
    Returns:
        dict: Comprehensive structural data
    """
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found")
        return None
    
    print(f"Analyzing ROSETTA silent file: {filename}")
    print("=" * 60)
    
    # Initialize data structures
    data = {
        'sequence': '',
        'models': [],
        'score_columns': [],
        'summary': {}
    }
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Extract sequence
    for line in lines:
        if line.startswith('SEQUENCE:'):
            data['sequence'] = line.split('SEQUENCE:')[1].strip()
            break
    
    # Extract score columns from header
    for line in lines:
        if line.startswith('SCORE:') and 'score' in line and 'fa_atr' in line:
            # This is the score header line
            score_parts = line.split()
            data['score_columns'] = score_parts[1:]  # Skip 'SCORE:'
            break
    
    # Extract model data
    current_model = None
    for line in lines:
        if line.startswith('SCORE:') and not line.startswith('SCORE:     score'):
            # This is a model score line
            parts = line.split()
            if len(parts) >= len(data['score_columns']) + 1:  # +1 for 'SCORE:'
                model_data = {}
                model_data['model_id'] = parts[-1]  # Last column is model ID
                
                # Parse score values
                for i, col in enumerate(data['score_columns']):
                    if i + 1 < len(parts):
                        try:
                            model_data[col] = float(parts[i + 1])
                        except ValueError:
                            model_data[col] = parts[i + 1]
                
                data['models'].append(model_data)
    
    # Generate summary statistics
    if data['models']:
        scores = [m.get('score', 0) for m in data['models'] if 'score' in m]
        n_bs = [m.get('N_BS', 0) for m in data['models'] if 'N_BS' in m]
        n_nwc = [m.get('N_NWC', 0) for m in data['models'] if 'N_NWC' in m]
        n_wc = [m.get('N_WC', 0) for m in data['models'] if 'N_WC' in m]
        
        data['summary'] = {
            'total_models': len(data['models']),
            'score_range': (min(scores), max(scores)) if scores else (0, 0),
            'base_pair_ranges': {
                'total': (min(n_bs), max(n_bs)) if n_bs else (0, 0),
                'non_watson_crick': (min(n_nwc), max(n_nwc)) if n_nwc else (0, 0),
                'watson_crick': (min(n_wc), max(n_wc)) if n_wc else (0, 0)
            }
        }
    
    return data

def print_analysis(data):
    """Print comprehensive analysis of ROSETTA output."""
    if not data:
        return
    
    print(f"Sequence Length: {len(data['sequence'])} nucleotides")
    print(f"Sequence: {data['sequence'][:50]}..." if len(data['sequence']) > 50 else f"Sequence: {data['sequence']}")
    print()
    
    print(f"Total Models Generated: {data['summary']['total_models']}")
    print()
    
    # Print score columns
    print("Score Components:")
    print("-" * 40)
    for i, col in enumerate(data['score_columns']):
        print(f"{i+1:2d}. {col}")
    print()
    
    # Print model details
    print("Model Details:")
    print("=" * 80)
    print(f"{'Model':<12} {'Score':<12} {'N_BS':<8} {'N_NWC':<8} {'N_WC':<8} {'Description':<20}")
    print("-" * 80)
    
    for model in data['models']:
        model_id = model.get('model_id', 'Unknown')
        score = model.get('score', 'N/A')
        n_bs = model.get('N_BS', 'N/A')
        n_nwc = model.get('N_NWC', 'N/A')
        n_wc = model.get('N_WC', 'N/A')
        description = f"Model {model_id}"
        
        print(f"{model_id:<12} {score:<12} {n_bs:<8} {n_nwc:<8} {n_wc:<8} {description:<20}")
    
    print()
    
    # Print summary statistics
    print("Summary Statistics:")
    print("-" * 40)
    print(f"Score Range: {data['summary']['score_range'][0]:.3f} to {data['summary']['score_range'][1]:.3f}")
    print(f"Total Base Pairs: {data['summary']['base_pair_ranges']['total'][0]} to {data['summary']['base_pair_ranges']['total'][1]}")
    print(f"Non-Watson-Crick: {data['summary']['base_pair_ranges']['non_watson_crick'][0]} to {data['summary']['base_pair_ranges']['non_watson_crick'][1]}")
    print(f"Watson-Crick: {data['summary']['base_pair_ranges']['watson_crick'][0]} to {data['summary']['base_pair_ranges']['watson_crick'][1]}")
    print()
    
    # Print detailed model information
    print("Detailed Model Information:")
    print("=" * 80)
    for model in data['models']:
        print(f"\nModel: {model.get('model_id', 'Unknown')}")
        print("-" * 40)
        for col in data['score_columns']:
            if col in model:
                value = model[col]
                if isinstance(value, float):
                    print(f"{col:<25}: {value:>10.3f}")
                else:
                    print(f"{col:<25}: {value:>10}")
        print()

def main():
    """Main function to run the analysis."""
    if len(sys.argv) != 2:
        print("Usage: python3 analyze_rosetta_output.py <silent_file.out>")
        print("Example: python3 analyze_rosetta_output.py tetrahymena_3d.out")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    # Parse the silent file
    data = parse_rosetta_silent_file(filename)
    
    if data:
        # Print the analysis
        print_analysis(data)
        
        # Save detailed results to file
        output_file = f"{os.path.splitext(filename)[0]}_analysis.txt"
        with open(output_file, 'w') as f:
            # Redirect stdout to file
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            print_analysis(data)
            
            # Get the output and restore stdout
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            # Write to file
            f.write(output)
        
        print(f"\nDetailed analysis saved to: {output_file}")
    else:
        print("Failed to parse ROSETTA silent file")
        sys.exit(1)

if __name__ == "__main__":
    main()
