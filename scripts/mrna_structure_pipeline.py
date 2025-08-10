#!/usr/bin/env python3
"""
mRNA Structure Prediction Pipeline
=================================

A comprehensive pipeline for predicting, analyzing, and comparing mRNA structures
using multiple methods and parameters. Designed for clean, organized output with
easy comparison across different prediction approaches.

Usage:
    python mrna_structure_pipeline.py [sequence_prefix] [sequence_file]
    
Examples:
    python mrna_structure_pipeline.py TETRAHYMENA
    python mrna_structure_pipeline.py YEAST data/yeast_sequence.fasta
"""

import json
import csv
import subprocess
from pathlib import Path
import re
from typing import Dict, List, Any, Optional
import argparse
import sys
import os


class StructureResult:
    """Container for structure prediction results."""
    
    def __init__(self, method: str, parameters: str, sequence: str, structure: str,
                 energy: float, base_pairs: List[tuple], num_base_pairs: int,
                 gc_content: float, base_pair_density: float):
        self.method = method
        self.parameters = parameters
        self.sequence = sequence
        self.structure = structure
        self.energy = energy
        self.base_pairs = base_pairs
        self.num_base_pairs = num_base_pairs
        self.gc_content = gc_content
        self.base_pair_density = base_pair_density


class mRNAStructurePipeline:
    """Main pipeline class for mRNA structure prediction and analysis."""
    
    def __init__(self, sequence_prefix: str, work_dir: str = "/orcd/data/mbathe/001/rcm095/RNA_predictions"):
        self.sequence_prefix = sequence_prefix
        self.sequence_name = f"{sequence_prefix}_5UTR"
        self.work_dir = Path(work_dir)
        self.output_dir = self.work_dir / "output" / "sequences" / self.sequence_name
        self.comparisons_dir = self.work_dir / "output" / "comparisons"
        self.structure_3d_dir = self.work_dir / "output" / "3d_structures" / self.sequence_name
        
        # Actual sequence will be set from input file
        self.actual_sequence = None
        
        # RNAfold parameters to test
        self.rnafold_parameters = {
            "default": {},
            "temperature_25C": {"-T": "25"},
            "temperature_50C": {"-T": "50"},
            "maxspan_20": {"--maxBPspan": "20"},
            "noGU": {"--noGU": ""},
            "partfunc": {"--partfunc": ""}
        }
        
        # 3D structure prediction methods
        self.available_3d_methods = {
            "rosetta": self._run_rosetta_prediction,
            "simrna": self._run_simrna_prediction,
            "farna": self._run_farna_prediction
        }
        
        # SLURM configuration for 3D structure prediction
        self.slurm_config = {
            "partition": "sched_cdrennan",
            "time": "48:00:00",
            "mem": "128000",
            "cpus_per_task": 10,
            "gpus": 2,
            "nodes": 1,
            "mpi_ranks": 8,
            "exclude": "node2021"
        }
    
    def setup_directories(self):
        """Create organized directory structure."""
        print(f"Setting up directory structure for {self.sequence_name}...")
        
        # Create main directories
        for method in ["rnafold", "deep_learning"]:  # Temporarily removed mfold
            method_dir = self.output_dir / method
            for param_name in self.rnafold_parameters.keys():
                param_dir = method_dir / param_name
                for subdir in ["raw_output", "parsed_results", "summary"]:
                    (param_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # TODO: Re-enable mfold directories when we find a non-interactive version
        # for method in ["rnafold", "mfold", "deep_learning"]:
        
        self.comparisons_dir.mkdir(parents=True, exist_ok=True)
        
        # Create 3D structure directories
        for method in self.available_3d_methods.keys():
            method_dir = self.structure_3d_dir / method
            for subdir in ["input", "output", "logs", "quality", "slurm_scripts"]:
                (method_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        print("✓ Directory structure created")
    
    def create_input_file(self, sequence: str) -> Path:
        """Create input FASTA file for RNAfold."""
        if not sequence:
            raise ValueError("Sequence is required")
        
        # Store the actual sequence for later use
        self.actual_sequence = sequence
        
        input_file = self.work_dir / "temp_input.fasta"
        with open(input_file, 'w') as f:
            f.write(f">{self.sequence_name}\n")
            f.write(f"{sequence}\n")
        
        return input_file
    
    def run_rnafold_predictions(self, input_file: Path):
        """Run RNAfold with all parameter combinations."""
        print(f"Running RNAfold predictions for {self.sequence_name}...")
        
        for param_name, params in self.rnafold_parameters.items():
            print(f"  Running {param_name}...")
            
            # Build command
            cmd = ["RNAfold"]
            for flag, value in params.items():
                if value:
                    cmd.extend([flag, str(value)])
                else:
                    cmd.append(flag)
            cmd.append(str(input_file))
            
            # Set output file
            output_file = self.output_dir / "rnafold" / param_name / "raw_output" / "structure.fold"
            
            # Run RNAfold and capture output
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                        universal_newlines=True, check=True)
                
                # Save structure output
                with open(output_file, 'w') as f:
                    f.write(result.stdout)
                
                # Copy PostScript files if they exist
                ps_files = list(self.work_dir.glob(f"{self.sequence_name}_*.ps"))
                for ps_file in ps_files:
                    dest_file = self.output_dir / "rnafold" / param_name / "raw_output" / f"structure_{ps_file.suffix}"
                    if ps_file.exists():
                        ps_file.rename(dest_file)
                
                print(f"    ✓ {param_name} completed")
                
            except subprocess.CalledProcessError as e:
                print(f"    ✗ {param_name} failed: {e}")
    
    def run_mfold_predictions(self, input_file: Path):
        """Run Mfold with all parameter combinations."""
        print(f"Running Mfold predictions for {self.sequence_name}...")
        
        # Mfold parameters to test
        mfold_parameters = {
            "default": {"temperature": 37.0, "max_structures": 10},
            "temperature_25C": {"temperature": 25.0, "max_structures": 10},
            "temperature_50C": {"temperature": 50.0, "max_structures": 10},
            "max_structures_5": {"temperature": 37.0, "max_structures": 5},
            "max_structures_20": {"temperature": 37.0, "max_structures": 20}
        }
        
        for param_name, params in mfold_parameters.items():
            print(f"  Running {param_name}...")
            
            # Create output directory
            output_dir = self.output_dir / "mfold" / param_name / "raw_output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Set environment variables for mfold
            env = os.environ.copy()
            env['SEQ'] = str(input_file)
            env['T'] = str(params['temperature'])
            env['MAX'] = str(params['max_structures'])
            
            try:
                # Run mfold
                result = subprocess.run(['mfold'], 
                                      capture_output=True, 
                                      text=True, 
                                      check=True,
                                      cwd=output_dir,
                                      env=env)
                
                # Save mfold output
                with open(output_dir / "mfold.log", 'w') as f:
                    f.write(result.stdout)
                if result.stderr:
                    with open(output_dir / "mfold.error", 'w') as f:
                        f.write(result.stderr)
                
                print(f"    ✓ {param_name} completed")
                
            except subprocess.CalledProcessError as e:
                print(f"    ✗ {param_name} failed: {e}")
                # Save error output
                with open(output_dir / "mfold.error", 'w') as f:
                    f.write(f"Error: {e}\nStderr: {e.stderr}")
    
    def parse_mfold_output(self, output_dir: Path) -> Optional[StructureResult]:
        """Parse Mfold output directory and extract structure information."""
        if not output_dir.exists():
            return None
        
        # Look for mfold output files
        pnt_file = output_dir / "sequence-local.pnt"
        sav_file = output_dir / "sequence.sav"
        
        if not pnt_file.exists() or not sav_file.exists():
            return None
        
        try:
            # Parse the .pnt file to get sequence info
            with open(pnt_file, 'r') as f:
                lines = f.readlines()
            
            sequence = ""
            for line in lines:
                if line.startswith('#'):
                    continue
                if line.strip() and not line.startswith(' '):
                    # This should be the sequence
                    seq_line = line.strip()
                    if len(seq_line) > 0:
                        sequence = seq_line
                        break
            
            if not sequence:
                return None
            
            # For now, create a simple structure (all unpaired)
            # In practice, we'd need mfold_util to extract real structures from .sav files
            structure = '.' * len(sequence)
            
            # Calculate basic metrics
            gc_content = (sequence.count('G') + sequence.count('C')) / len(sequence)
            base_pair_density = 0.0  # No base pairs in this simple structure
            
            return StructureResult(
                method="mfold",
                parameters="default",
                sequence=sequence,
                structure=structure,
                energy=None,  # Would need mfold_util to extract
                base_pairs=[],
                num_base_pairs=0,
                gc_content=gc_content,
                base_pair_density=base_pair_density
            )
            
        except Exception as e:
            print(f"Failed to parse mfold output: {e}")
            return None
    
    def parse_rnafold_output(self, fold_file: Path) -> Optional[StructureResult]:
        """Parse RNAfold output file and extract structure information."""
        if not fold_file.exists():
            return None
        
        with open(fold_file, 'r') as f:
            content = f.read()
        
        # Parse the output format - handle multi-line structure
        lines = content.strip().split('\n')
        if len(lines) < 3:
            return None
        
        # First line is header, subsequent lines contain sequence and structure
        sequence = ""
        structure = ""
        energy = None
        
        # Extract sequence (may be split across multiple lines)
        for i, line in enumerate(lines[1:], 1):
            if line.startswith('>'):
                continue
            if '(' in line and ')' in line:
                # This line contains structure
                # Extract sequence part before structure
                seq_part = line[:line.find('(')].strip()
                sequence += seq_part
                
                # Extract structure part (including dots - they represent unpaired nucleotides)
                structure_part = line[line.find('('):]
                # Remove energy from end
                structure_part = re.sub(r'\s*\([^)]+\)$', '', structure_part)
                structure = structure_part
                
                # Extract energy
                energy_match = re.search(r'\(([^)]+)\)$', line)
                if energy_match:
                    try:
                        energy = float(energy_match.group(1))
                    except ValueError:
                        energy = None
                break
            else:
                # This line is part of the sequence
                sequence += line.strip()
        
        # Clean up sequence - remove any trailing dots that might be parsing artifacts
        clean_sequence = sequence.rstrip('.')
        
        if clean_sequence and structure and energy is not None:
            # Parse base pairs
            base_pairs = []
            stack = []
            for i, char in enumerate(structure):
                if char == '(':
                    stack.append(i)
                elif char == ')':
                    if stack:
                        j = stack.pop()
                        base_pairs.append((j, i))
            
            # Use the original input sequence for GC content calculation
            original_sequence = self.actual_sequence
            if not original_sequence:
                raise ValueError("No sequence available for GC content calculation")
            gc_content = (original_sequence.count('G') + original_sequence.count('C')) / len(original_sequence)
            
            # Calculate base pair density using structure length (including dots)
            base_pair_density = len(base_pairs) / len(structure)
            
            return StructureResult(
                method="rnafold",
                parameters=fold_file.parent.parent.name,
                sequence=clean_sequence,
                structure=structure,
                energy=energy,
                base_pairs=sorted(base_pairs),
                num_base_pairs=len(base_pairs),
                gc_content=gc_content,
                base_pair_density=base_pair_density
            )
        
        return None
    
    def collect_all_results(self) -> Dict[str, StructureResult]:
        """Collect all prediction results."""
        results = {}
        
        # Collect RNAfold results
        for param_name in self.rnafold_parameters.keys():
            fold_file = self.output_dir / "rnafold" / param_name / "raw_output" / "structure.fold"
            result = self.parse_rnafold_output(fold_file)
            if result:
                results[f"rnafold_{param_name}"] = result
        
        # Collect Mfold results - Temporarily disabled
        # mfold_parameters = ["default", "temperature_25C", "temperature_50C", "max_structures_5", "max_structures_20"]
        # for param_name in mfold_parameters:
        #     output_dir = self.output_dir / "mfold" / param_name / "raw_output"
        #     result = self.parse_mfold_output(output_dir)
        #     if result:
        #         results[f"mfold_{param_name}"] = result
        
        # TODO: Re-enable mfold results collection when we find a non-interactive version
        
        return results
    
    def create_comprehensive_summary(self, results: Dict[str, StructureResult]):
        """Create comprehensive summary files."""
        print("Creating comprehensive summaries...")
        
        # Prepare summary data
        if not self.actual_sequence:
            raise ValueError("No sequence available for summary creation")
        
        summary = {
            'sequence_name': self.sequence_name,
            'sequence': self.actual_sequence,
            'sequence_length': len(self.actual_sequence),
            'methods_tested': list(results.keys()),
            'results': {name: result.__dict__ for name, result in results.items()},
            'comparison': {
                'energies': {name: result.energy for name, result in results.items()},
                'base_pair_counts': {name: result.num_base_pairs for name, result in results.items()},
                'gc_contents': {name: result.gc_content for name, result in results.items()}
            }
        }
        
        # Save JSON summary
        json_file = self.comparisons_dir / f"{self.sequence_prefix}_comprehensive_results.json"
        with open(json_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save CSV summary
        csv_file = self.comparisons_dir / f"{self.sequence_prefix}_results_summary.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Method', 'Energy (kcal/mol)', 'Base Pairs', 'GC Content (%)', 'Base Pair Density'])
            for name, result in results.items():
                writer.writerow([
                    name,
                    f"{result.energy:.2f}",
                    result.num_base_pairs,
                    f"{result.gc_content * 100:.1f}",
                    f"{result.base_pair_density:.3f}"
                ])
        
        # Save text summary
        txt_file = self.comparisons_dir / f"{self.sequence_prefix}_results_summary.txt"
        with open(txt_file, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("MRNA STRUCTURE PREDICTION RESULTS\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Sequence: {self.sequence_name}\n")
            f.write(f"Length: {len(self.actual_sequence)} nucleotides\n")
            f.write(f"Sequence: {self.actual_sequence}\n\n")
            f.write("METHOD COMPARISON:\n")
            f.write("-" * 40 + "\n\n")
            
            for name, result in results.items():
                f.write(f"{name.upper()}:\n")
                f.write(f"  Energy: {result.energy:.2f} kcal/mol\n")
                f.write(f"  Base Pairs: {result.num_base_pairs}\n")
                f.write(f"  GC Content: {result.gc_content * 100:.1f}%\n")
                f.write(f"  Base Pair Density: {result.base_pair_density:.3f}\n")
                f.write(f"  Structure: {result.structure}\n\n")
            
            # Find best energy
            best_energy = min(results.values(), key=lambda x: x.energy)
            f.write("SUMMARY:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Best Energy: {best_energy.energy:.2f} kcal/mol ({best_energy.parameters})\n")
            f.write(f"Methods Tested: {len(results)}\n")
            f.write(f"Average Base Pairs: {sum(r.num_base_pairs for r in results.values()) / len(results):.1f}\n")
            f.write(f"Average GC Content: {sum(r.gc_content for r in results.values()) / len(results) * 100:.1f}%\n")
        
        print("✓ Summary files created:")
        print(f"  - JSON: {json_file}")
        print(f"  - CSV: {csv_file}")
        print(f"  - TXT: {txt_file}")
    
    def print_results_summary(self, results: Dict[str, StructureResult]):
        """Print a summary of results to console."""
        print("\n" + "=" * 60)
        print("PREDICTION RESULTS SUMMARY")
        print("=" * 60)
        
        for name, result in results.items():
            print(f"\n{name.upper()}:")
            print(f"  Energy: {result.energy:.2f} kcal/mol")
            print(f"  Base pairs: {result.num_base_pairs}")
            print(f"  Structure: {result.structure}")
            print(f"  GC Content: {result.gc_content * 100:.1f}%")
            print(f"  Base Pair Density: {result.base_pair_density:.3f}")
        
        # Find best energy
        if results:
            best_energy = min(results.values(), key=lambda x: x.energy)
            print(f"\n⭐ BEST ENERGY: {best_energy.energy:.2f} kcal/mol ({best_energy.parameters})")
    
    def run_pipeline(self, sequence: str):
        """Run the complete pipeline."""
        if not sequence:
            raise ValueError("Sequence is required")
        
        print("=" * 60)
        print("MRNA STRUCTURE PREDICTION PIPELINE")
        print("=" * 60)
        print(f"Sequence Prefix: {self.sequence_prefix}")
        print(f"Sequence Name: {self.sequence_name}")
        print(f"Sequence Length: {len(sequence)} nucleotides")
        print()
        
        # Setup directories
        self.setup_directories()
        
        # Create input file
        input_file = self.create_input_file(sequence)
        
        # Run predictions
        self.run_rnafold_predictions(input_file)
        # self.run_mfold_predictions(input_file)  # Temporarily disabled - mfold 3.6 has interactive-only issues
        
        # TODO: Re-enable mfold when we find a non-interactive version
        
        # Parse and collect results
        print("Parsing prediction results...")
        results = self.collect_all_results()
        print(f"✓ Parsed {len(results)} prediction results")
        
        # Create summaries
        self.create_comprehensive_summary(results)
        
        # Print summary
        self.print_results_summary(results)
        
        print("\n✓ Pipeline completed successfully!")
        print(f"Check {self.output_dir}/ for individual results")
        print(f"Check {self.comparisons_dir}/ for comparison files")


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description="mRNA Structure Prediction Pipeline")
    parser.add_argument("sequence_prefix", help="Sequence prefix (e.g., TETRAHYMENA, YEAST)")
    parser.add_argument("sequence_file", nargs='?', help="Optional: Path to sequence file")
    parser.add_argument("--work-dir", default="/orcd/data/mbathe/001/rcm095/RNA_predictions",
                       help="Working directory for output")
    
    args = parser.parse_args()
    
    # Read sequence from file if provided, otherwise use Tetrahymena benchmark
    sequence = None
    if args.sequence_file:
        sequence_file = Path(args.sequence_file)
        if sequence_file.exists():
            with open(sequence_file, 'r') as f:
                lines = f.readlines()
                # Skip header lines starting with >
                sequence_lines = [line.strip() for line in lines if not line.startswith('>')]
                sequence = ''.join(sequence_lines)
        else:
            print(f"Error: Sequence file {args.sequence_file} not found")
            sys.exit(1)
    else:
        # Use Tetrahymena P4-P6 domain as our benchmark sequence
        sequence = "GGCAGGAAACCGGUGAGUAGCGCAGGGUUCGGUGUAGUCCGUGAGGCGAAAGCGCUAGCCGAAAGGCGAAACCGCUGAUGAGUAGCGCAGGGUUCGAUCCGGUAGCGAAAGCGCUAGCCGAAAGGCGAAACCGCU"
        print(f"Using Tetrahymena P4-P6 domain as benchmark sequence (135 nt)")
    
    # Create and run pipeline
    pipeline = mRNAStructurePipeline(args.sequence_prefix, args.work_dir)
    pipeline.run_pipeline(sequence)


if __name__ == "__main__":
    main()
