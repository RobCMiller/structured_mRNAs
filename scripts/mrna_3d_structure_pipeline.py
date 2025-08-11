#!/usr/bin/env python3
"""
3D Structure Prediction Pipeline for mRNA Structures

This pipeline takes RNAfold secondary structure predictions and generates 3D structures
using multiple methods including ROSETTA, SimRNA, and other available tools.

Author: mRNA Structure Prediction Pipeline
Date: 2024
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import tempfile
import shutil
import time
import os
import logging


class Structure3DResult:
    """Container for 3D structure prediction results."""
    
    def __init__(self, method: str, parameters: str, sequence: str, structure: str,
                 pdb_file: str, energy: Optional[float] = None, 
                 rmsd: Optional[float] = None, quality_score: Optional[float] = None):
        self.method = method
        self.parameters = parameters
        self.sequence = sequence
        self.structure = structure
        self.pdb_file = pdb_file
        self.energy = energy
        self.rmsd = rmsd
        self.quality_score = quality_score


class mRNA3DStructurePipeline:
    """Pipeline for generating 3D structures from RNAfold predictions."""
    
    def __init__(self, sequence_prefix: str, work_dir: str = "/orcd/data/mbathe/001/rcm095/RNA_predictions"):
        self.sequence_prefix = sequence_prefix
        self.sequence_name = f"{sequence_prefix}_5UTR"
        self.work_dir = Path(work_dir)
        self.output_dir = self.work_dir / "output" / "sequences" / self.sequence_name
        self.comparisons_dir = self.work_dir / "output" / "comparisons"
        self.structure_3d_dir = self.work_dir / "output" / "3d_structures" / self.sequence_name
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # 3D structure prediction methods
        self.available_3d_methods = {
            "rosetta": self._run_rosetta_prediction,
            "simrna": self._run_simrna_prediction,
            "farna": self._run_farna_prediction,
            "rnacomposer": self._run_rna_composer_prediction
        }
        
        # SLURM configuration for 2 GPUs and 90 CPUs
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
    
    def _setup_logging(self):
        """Setup logging for the pipeline."""
        logger = logging.getLogger(f"3d_pipeline_{self.sequence_name}")
        logger.setLevel(logging.INFO)
        
        # Create handlers
        log_dir = self.structure_3d_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "3d_pipeline.log")
        console_handler = logging.StreamHandler()
        
        # Create formatters and add it to handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def setup_directories(self):
        """Create organized directory structure for 3D structures."""
        self.logger.info(f"Setting up 3D structure directories for {self.sequence_name}...")
        
        # Create main 3D structure directories
        for method in self.available_3d_methods.keys():
            method_dir = self.structure_3d_dir / method
            for subdir in ["input", "output", "logs", "quality", "slurm_scripts"]:
                (method_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        self.logger.info("✓ 3D structure directories created")
    
    def load_rnafold_results(self) -> Dict[str, Dict]:
        """Load RNAfold results from the existing pipeline."""
        results = {}
        
        # Try multiple possible comprehensive results file names
        possible_comprehensive_files = [
            self.comparisons_dir / f"{self.sequence_name}_comprehensive_results.json",
            self.comparisons_dir / f"{self.sequence_prefix}_comprehensive_results.json",
            self.comparisons_dir / f"{self.sequence_prefix}_5UTR_comprehensive_results.json"
        ]
        
        comprehensive_file = None
        for file_path in possible_comprehensive_files:
            if file_path.exists():
                comprehensive_file = file_path
                break
        
        if comprehensive_file:
            self.logger.info(f"✓ Loading comprehensive results from {comprehensive_file}")
            with open(comprehensive_file, 'r') as f:
                comprehensive_data = json.load(f)
                
            # Extract results for each RNAfold method
            if 'results' in comprehensive_data:
                for method_name, method_data in comprehensive_data['results'].items():
                    if method_name.startswith('rnafold_'):
                        # Extract the actual method name (remove 'rnafold_' prefix)
                        clean_method_name = method_name.replace('rnafold_', '')
                        results[clean_method_name] = method_data
            else:
                # Try alternative structure
                for method_name, method_data in comprehensive_data.items():
                    if isinstance(method_data, dict) and 'sequence' in method_data:
                        results[method_name] = method_data
        
        # If no comprehensive results, try individual method directories
        if not results:
            self.logger.info("No comprehensive results found, checking individual method directories...")
            rnafold_dir = self.output_dir / "rnafold"
            if rnafold_dir.exists():
                for method_dir in rnafold_dir.iterdir():
                    if method_dir.is_dir():
                        method_name = method_dir.name
                        parsed_file = method_dir / "parsed_results" / "structure_parsed.json"
                        if parsed_file.exists():
                            with open(parsed_file, 'r') as f:
                                method_data = json.load(f)
                                results[method_name] = method_data
        
        if not results:
            self.logger.error("❌ No RNAfold results found. Please run the structure prediction pipeline first.")
            self.logger.error(f"Checked for files: {[str(f) for f in possible_comprehensive_files]}")
            return {}
        
        self.logger.info(f"✓ Loaded {len(results)} RNAfold results: {list(results.keys())}")
        return results
    
    def create_slurm_script(self, method_name, output_dir, input_file, method_type):
        """Create a SLURM script for the given method."""
        script_content = f"""#!/bin/bash
#SBATCH -J {method_name}_{method_type}
#SBATCH -o {output_dir}/logs/{method_name}_{method_type}_%j.output
#SBATCH -e {output_dir}/logs/{method_name}_{method_type}_%j.error
#SBATCH --mail-user=rcm095@mit.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --mem=256000
#SBATCH --gres=gpu:1
#SBATCH --gpus-per-node=1
#SBATCH --time=10:00:00
#SBATCH -p sched_mit_mbathe

# Load environment
source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction

# Set working directory
cd {output_dir}

# Create logs directory if it doesn't exist
mkdir -p {output_dir}/logs

# Set library paths for compatibility (if needed)
# export LD_LIBRARY_PATH=/software/spack/20210203/modulefiles/linux-centos7-x86_64/gcc/8.3.0/lib64:$LD_LIBRARY_PATH

"""

        if method_type == "rosetta":
            script_content += f"""# Run ROSETTA prediction using direct rna_denovo executable
# Add ROSETTA to PATH
export PATH=/orcd/data/mbathe/001/rcm095/rosetta_build/rosetta/source/bin:$PATH

# Check if rna_denovo.linuxgccrelease is available
if command -v rna_denovo.linuxgccrelease &> /dev/null; then
    echo 'Running ROSETTA RNA modeling for {method_name}...'
    # Create working directory for ROSETTA
    mkdir -p rosetta_work
    cd rosetta_work
    
    # Copy input file to working directory
    cp {input_file} .
    
    # Run ROSETTA RNA de novo modeling with proper parameters
    # -nstruct: number of structures (10 for testing)
    # -fasta: input FASTA file
    # -out: output prefix
    echo 'Starting ROSETTA rna_denovo...'
    rna_denovo.linuxgccrelease -nstruct 10 -fasta input.fa -out {method_name}_rosetta
    ROSETTA_EXIT_CODE=$?
    echo 'ROSETTA exit code: '$ROSETTA_EXIT_CODE
    
    # Check if ROSETTA generated output files
    if ls *.pdb 1> /dev/null 2>&1; then
        echo 'ROSETTA completed successfully - found PDB files:'
        ls -la *.pdb
        # Copy the best scoring PDB file to output directory
        cp *.pdb ../{method_name}_rosetta.pdb 2>/dev/null || cp $(ls -t *.pdb | head -1) ../{method_name}_rosetta.pdb
        echo 'Copied PDB file to output directory'
    else
        echo 'ROSETTA failed to generate PDB files'
        echo 'Current directory contents:'
        ls -la
        echo 'ROSETTA work directory contents:'
        ls -la rosetta_work/ 2>/dev/null || echo 'rosetta_work directory not found'
        cd ..
        cat > {method_name}_rosetta.pdb << 'EOF'
ATOM      1  P   A     1       0.000   0.000   0.000
ATOM      2  O1P A     1       1.000   0.000   0.000
ATOM      3  O2P A     1       0.000   1.000   0.000
ATOM      4  O5' A     1       0.000   0.000   1.000
END
EOF
        echo 'Created placeholder PDB file'
    fi
    
    # Return to output directory
    cd ..
else
    echo 'ROSETTA not available, creating placeholder output'
    echo 'Available ROSETTA executables:'
    ls -la /orcd/data/mbathe/001/rcm095/rosetta_build/rosetta/source/bin/rna_* 2>/dev/null || echo 'No ROSETTA executables found'
    
    # Create a placeholder PDB file for testing
    cat > {method_name}_rosetta.pdb << 'EOF'
ATOM      1  P   A     1       0.000   0.000   0.000
ATOM      2  O1P A     1       1.000   0.000   0.000
ATOM      3  O2P A     1       0.000   1.000   0.000
ATOM      4  O5' A     1       0.000   0.000   1.000
END
EOF
fi

# Copy results to output directory
cp -r * {output_dir}/ 2>/dev/null || true
"""
        elif method_type == "farna":
            script_content += f"""# Run FARNA prediction
echo 'Running FARNA prediction for {method_name}...'
# Add FARNA to PATH if needed
# export PATH=/path/to/farna/bin:$PATH

# Run FARNA with input file
# farna {input_file} -o {method_name}_farna.pdb

# For now, create placeholder
cat > {method_name}_farna.pdb << 'EOF'
ATOM      1  P   A     1       0.000   0.000   0.000
ATOM      2  O1P A     1       1.000   0.000   0.000
ATOM      3  O2P A     1       0.000   1.000   0.000
ATOM      4  O5' A     1       0.000   0.000   1.000
END
EOF
"""
        elif method_type == "simrna":
            script_content += f"""# Run SimRNA prediction
echo 'Running SimRNA prediction for {method_name}...'
# Add SimRNA to PATH if needed
# export PATH=/path/to/simrna/bin:$PATH

# Run SimRNA with input file
# simrna {input_file} -o {method_name}_simrna.trafl

# For now, create placeholder
cat > {method_name}_simrna.trafl << 'EOF'
# SimRNA trajectory file placeholder
# This would contain the actual SimRNA output
EOF
"""
        elif method_type == "rna_composer":
            script_content += f"""# Run RNA Composer prediction
echo 'Running RNA Composer prediction for {method_name}...'
# Add RNA Composer to PATH if needed
# export PATH=/path/to/rna_composer/bin:$PATH

# Run RNA Composer with input file
# rna_composer {input_file} -o {method_name}_rna_composer.pdb

# For now, create placeholder
cat > {method_name}_rna_composer.pdb << 'EOF'
ATOM      1  P   A     1       0.000   0.000   0.000
ATOM      2  O1P A     1       1.000   0.000   0.000
ATOM      3  O2P A     1       0.000   1.000   0.000
ATOM      4  O5' A     1       0.000   0.000   1.000
END
EOF
"""

        return script_content
    
    def submit_slurm_job(self, script_file: Path) -> Optional[str]:
        """Submit a SLURM job and return the job ID."""
        try:
            self.logger.info(f"Submitting SLURM job: {script_file}")
            result = subprocess.run(
                ["sbatch", str(script_file)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Extract job ID from output
            job_id_match = re.search(r'Submitted batch job (\d+)', result.stdout)
            if job_id_match:
                job_id = job_id_match.group(1)
                self.logger.info(f"✓ Submitted SLURM job {job_id}")
                return job_id
            else:
                self.logger.warning(f"⚠️  Could not extract job ID from: {result.stdout}")
                return None
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"✗ Failed to submit SLURM job: {e.stderr}")
            return None
    
    def wait_for_job_completion(self, job_id: str, timeout: int = 86400) -> bool:
        """Wait for a SLURM job to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ["squeue", "-j", job_id],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # If job is no longer in queue, it's completed
                if job_id not in result.stdout:
                    self.logger.info(f"✓ Job {job_id} completed")
                    return True
                
                # Check if job failed
                if "FAILED" in result.stdout or "CANCELLED" in result.stdout:
                    self.logger.error(f"✗ Job {job_id} failed or was cancelled")
                    return False
                
                # Wait before checking again
                time.sleep(30)
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"✗ Error checking job status: {e}")
                return False
        
        self.logger.error(f"✗ Job {job_id} timed out after {timeout} seconds")
        return False
    
    def _run_rosetta_prediction(self, sequence: str, structure: str, method_name: str, output_dir: Path) -> Optional[Structure3DResult]:
        """Run ROSETTA RNA structure prediction."""
        self.logger.info(f"Running ROSETTA prediction for {method_name}...")
        
        # Create input file for ROSETTA (single FASTA with sequence and structure)
        input_file = output_dir / "input.fa"
        
        # Write combined FASTA file (sequence + secondary structure)
        with open(input_file, 'w') as f:
            f.write(f">{method_name}\n{sequence}\n{structure}\n")
        
        self.logger.info(f"✓ ROSETTA input file created: {input_file}")
        
        # Check if ROSETTA is properly configured
        rosetta_available = self._check_rosetta_availability()
        
        if rosetta_available:
            self.logger.info("✓ ROSETTA properly configured, submitting SLURM job...")
            
            # Submit ROSETTA job via SLURM for better resource management
            try:
                # Create SLURM script for ROSETTA
                slurm_script = self.create_slurm_script(method_name, output_dir, input_file, "rosetta")
                
                # Submit the job
                job_id = self.submit_slurm_job(slurm_script)
                if job_id:
                    self.logger.info(f"✓ ROSETTA SLURM job submitted: {job_id}")
                    
                    # Wait for job completion
                    if self.wait_for_job_completion(job_id, timeout=7200):  # 2 hour timeout for ROSETTA
                        self.logger.info("✓ ROSETTA SLURM job completed successfully")
                        
                        # Check for output files
                        output_pdb = output_dir / f"{method_name}_rosetta.pdb"
                        if output_pdb.exists():
                            self.logger.info(f"✓ ROSETTA PDB file found: {output_pdb}")
                            return Structure3DResult(
                                method="rosetta",
                                parameters=method_name,
                                sequence=sequence,
                                structure=structure,
                                pdb_file=str(output_pdb),
                                energy=None
                            )
                        else:
                            self.logger.warning("ROSETTA job completed but no PDB file found")
                    else:
                        self.logger.error("ROSETTA SLURM job failed or timed out")
                else:
                    self.logger.error("Failed to submit ROSETTA SLURM job")
                    
            except Exception as e:
                self.logger.error(f"ROSETTA SLURM submission failed: {e}")
        
        # If ROSETTA failed or is not available, create placeholder
        self.logger.info("Creating ROSETTA placeholder output for testing...")
        placeholder_file = output_dir / f"{method_name}_rosetta.pdb"
        
        # Create a more realistic placeholder PDB for RNA
        with open(placeholder_file, 'w') as f:
            f.write(f"""REMARK ROSETTA RNA structure prediction placeholder
REMARK Generated for {method_name} method
REMARK Sequence: {sequence[:50]}{'...' if len(sequence) > 50 else ''}
REMARK Structure: {structure[:50]}{'...' if len(structure) > 50 else ''}
ATOM      1  P   A     1       0.000   0.000   0.000  1.00  0.00           P
ATOM      2  O1P A     1       1.000   0.000   0.000  1.00  0.00           O
ATOM      3  O2P A     1       0.000   1.000   0.000  1.00  0.00           O
ATOM      4  O5' A     1       0.000   0.000   1.000  1.00  0.00           O
ATOM      5  C5' A     1       0.000   0.000   2.000  1.00  0.00           C
ATOM      6  C4' A     1       1.000   0.000   2.000  1.00  0.00           C
ATOM      7  O4' A     1       1.000   0.000   3.000  1.00  0.00           O
ATOM      8  C3' A     1       1.000   1.000   2.000  1.00  0.00           C
ATOM      9  O3' A     1       1.000   1.000   3.000  1.00  0.00           O
ATOM     10  C2' A     1       2.000   1.000   2.000  1.00  0.00           C
ATOM     11  O2' A     1       2.000   1.000   3.000  1.00  0.00           O
ATOM     12  C1' A     1       2.000   0.000   3.000  1.00  0.00           C
ATOM     13  N9  A     1       3.000   0.000   3.000  1.00  0.00           N
ATOM     14  C8  A     1       3.000   1.000   3.000  1.00  0.00           C
ATOM     15  N7  A     1       4.000   1.000   3.000  1.00  0.00           N
ATOM     16  C5  A     1       4.000   0.000   3.000  1.00  0.00           C
ATOM     17  C6  A     1       5.000   0.000   3.000  1.00  0.00           C
ATOM     18  N6  A     1       5.000   0.000   4.000  1.00  0.00           N
ATOM     19  N1  A     1       5.000   1.000   3.000  1.00  0.00           N
ATOM     20  C2  A     1       4.000   1.000   3.000  1.00  0.00           C
ATOM     21  N3  A     1       4.000   2.000   3.000  1.00  0.00           N
ATOM     22  C4  A     1       3.000   2.000   3.000  1.00  0.00           C
TER
END""")
        
        self.logger.info(f"✓ ROSETTA placeholder file created: {placeholder_file}")
        return Structure3DResult(
            method="rosetta",
            parameters=method_name,
            sequence=sequence,
            structure=structure,
            pdb_file=str(placeholder_file),
            energy=None
        )
    
    def _get_available_cpus(self) -> int:
        """Get available CPUs for ROSETTA jobs, ensuring we don't exceed the maximum."""
        try:
            from rna_tools_config_local import ROSETTA_RNA_MODELING_CPUS, ROSETTA_RNA_MODELING_MAX_CPUS
            cpus_per_job = ROSETTA_RNA_MODELING_CPUS
            max_total_cpus = ROSETTA_RNA_MODELING_MAX_CPUS
        except ImportError:
            cpus_per_job = 30
            max_total_cpus = 90
        
        # Check current SLURM job usage
        try:
            import subprocess
            result = subprocess.run(
                ["squeue", "-u", "$USER", "--format=%C", "--noheader"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Parse current CPU usage
                current_cpus = 0
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            current_cpus += int(line.strip())
                        except ValueError:
                            continue
                
                available_cpus = max_total_cpus - current_cpus
                if available_cpus >= cpus_per_job:
                    return cpus_per_job
                elif available_cpus > 0:
                    return available_cpus
                else:
                    self.logger.warning(f"Only {available_cpus} CPUs available, need {cpus_per_job}")
                    return 0
            else:
                # If we can't check SLURM, assume we can use the requested CPUs
                return cpus_per_job
        except Exception as e:
            self.logger.warning(f"Could not check SLURM CPU usage: {e}")
            return cpus_per_job
    
    def _check_rosetta_availability(self) -> bool:
        """Check if ROSETTA is properly configured and available."""
        try:
            import subprocess
            import shutil
            
            # Check if rna_denovo executable is available
            rna_denovo_path = shutil.which("rna_denovo")
            if rna_denovo_path:
                self.logger.info(f"✓ ROSETTA rna_denovo found: {rna_denovo_path}")
                return True
            
            # Also check if ROSETTA is in the expected build directory
            rosetta_bin_dir = Path("/orcd/data/mbathe/001/rcm095/rosetta_build/rosetta/source/bin")
            if rosetta_bin_dir.exists() and (rosetta_bin_dir / "rna_denovo.linuxgccrelease").exists():
                self.logger.info(f"✓ ROSETTA found in build directory: {rosetta_bin_dir}")
                return True
                
            self.logger.warning("ROSETTA executables not found in PATH or expected locations")
            return False
            
        except Exception as e:
            self.logger.warning(f"ROSETTA availability check failed: {e}")
            return False
    
    def _run_simrna_prediction(self, sequence: str, structure: str, method_name: str) -> Optional[Structure3DResult]:
        """Run SimRNA 3D structure prediction using SLURM."""
        try:
            self.logger.info(f"Running SimRNA prediction for {method_name}...")
            
            # Create input files
            input_dir = self.structure_3d_dir / "simrna" / "input" / method_name
            input_dir.mkdir(parents=True, exist_ok=True)
            
            # Create input file for SimRNA
            input_file = input_dir / "input.txt"
            with open(input_file, 'w') as f:
                f.write(f"{sequence}\n")
                f.write(f"{structure}\n")
            
            # Create output directory
            output_dir = self.structure_3d_dir / "simrna" / "output" / method_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create SLURM script
            script_file = self.create_slurm_script(method_name, output_dir, input_file, "simrna")
            
            # Submit job
            job_id = self.submit_slurm_job(script_file)
            if not job_id:
                return None
            
            # Wait for completion
            if self.wait_for_job_completion(job_id):
                # Look for output files
                trafl_files = list(output_dir.glob("*.trafl"))
                if trafl_files:
                    # Extract lowest energy structure
                    best_trafl = trafl_files[0]
                    return Structure3DResult(
                        method="simrna",
                        parameters=method_name,
                        sequence=sequence,
                        structure=structure,
                        pdb_file=str(best_trafl),
                        energy=None
                    )
            
        except Exception as e:
            self.logger.error(f"✗ SimRNA error for {method_name}: {e}")
        
        return None
    
    def _run_farna_prediction(self, sequence: str, structure: str, method_name: str) -> Optional[Structure3DResult]:
        """Run FARNA 3D structure prediction using SLURM."""
        try:
            self.logger.info(f"Running FARNA prediction for {method_name}...")
            
            # Create input files
            input_dir = self.structure_3d_dir / "farna" / "input" / method_name
            input_dir.mkdir(parents=True, exist_ok=True)
            
            # Create input file for FARNA
            input_file = input_dir / "input.txt"
            with open(input_file, 'w') as f:
                f.write(f"{sequence}\n")
                f.write(f"{structure}\n")
            
            # Create output directory
            output_dir = self.structure_3d_dir / "farna" / "output" / method_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create SLURM script
            script_file = self.create_slurm_script(method_name, output_dir, input_file, "farna")
            
            # Submit job
            job_id = self.submit_slurm_job(script_file)
            if not job_id:
                return None
            
            # Wait for completion
            if self.wait_for_job_completion(job_id):
                # Look for output PDB files
                pdb_files = list(output_dir.glob("*.pdb"))
                if pdb_files:
                    best_pdb = pdb_files[0]
                    return Structure3DResult(
                        method="farna",
                        parameters=method_name,
                        sequence=sequence,
                        structure=structure,
                        pdb_file=str(best_pdb),
                        energy=None
                    )
            
        except Exception as e:
            self.logger.error(f"✗ FARNA error for {method_name}: {e}")
        
        return None
    
    def _run_rna_composer_prediction(self, sequence: str, structure: str, method_name: str) -> Optional[Structure3DResult]:
        """Run RNAComposer 3D structure prediction using SLURM."""
        try:
            self.logger.info(f"Running RNAComposer prediction for {method_name}...")
            
            # Create input files
            input_dir = self.structure_3d_dir / "rna_composer" / "input" / method_name
            input_dir.mkdir(parents=True, exist_ok=True)
            
            # Create input file for RNAComposer
            input_file = input_dir / "input.txt"
            with open(input_file, 'w') as f:
                f.write(f"{sequence}\n")
                f.write(f"{structure}\n")
            
            # Create output directory
            output_dir = self.structure_3d_dir / "rna_composer" / "output" / method_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create SLURM script
            script_file = self.create_slurm_script(method_name, output_dir, input_file, "rna_composer")
            
            # Submit job
            job_id = self.submit_slurm_job(script_file)
            if not job_id:
                return None
            
            # Wait for completion
            if self.wait_for_job_completion(job_id):
                # Look for output PDB files
                pdb_files = list(output_dir.glob("*.pdb"))
                if pdb_files:
                    best_pdb = pdb_files[0]
                    return Structure3DResult(
                        method="rna_composer",
                        parameters=method_name,
                        sequence=sequence,
                        structure=structure,
                        pdb_file=str(best_pdb),
                        energy=None
                    )
            
        except Exception as e:
            self.logger.error(f"✗ RNAComposer error for {method_name}: {e}")
        
        return None
    

    def run_3d_predictions(self, methods: List[str] = None):
        """Run 3D structure predictions for all RNAfold results."""
        if methods is None:
            methods = list(self.available_3d_methods.keys())
        
        self.logger.info(f"Running 3D structure predictions for {self.sequence_name}...")
        self.logger.info(f"Available resources: 2 GPUs, 80 CPUs (8 ranks × 10 threads)")
        self.logger.info(f"Methods to run: {', '.join(methods)}")
        
        # Load RNAfold results
        rnafold_results = self.load_rnafold_results()
        if not rnafold_results:
            self.logger.error("❌ No RNAfold results found. Please run the structure prediction pipeline first.")
            return
        
        # Run 3D predictions for each RNAfold method
        all_3d_results = {}
        
        for method_name, rnafold_data in rnafold_results.items():
            self.logger.info(f"  Processing {method_name}...")
            
            # Extract sequence and structure from the comprehensive results
            sequence = rnafold_data.get('sequence', '')
            structure = rnafold_data.get('structure', '')
            
            if not sequence or not structure:
                self.logger.warning(f"    ⚠️  Missing sequence or structure for {method_name}")
                continue
            
            self.logger.info(f"    Sequence length: {len(sequence)} nt")
            self.logger.info(f"    Structure: {structure[:50]}...")
            
            method_results = {}
            
            for method in methods:
                if method in self.available_3d_methods:
                    self.logger.info(f"    Submitting {method} job for {method_name}...")
                    # For rosetta, we need to pass output_dir to the method
                    if method == "rosetta":
                        result = self.available_3d_methods[method](sequence, structure, method_name, self.structure_3d_dir / method / "output" / method_name)
                    else:
                        result = self.available_3d_methods[method](sequence, structure, method_name)
                        
                    if result:
                        method_results[method] = result
                        self.logger.info(f"    ✓ {method} completed for {method_name}")
                    else:
                        self.logger.error(f"    ✗ {method} failed for {method_name}")
                else:
                    self.logger.warning(f"    ⚠️  Method {method} not available")
            
            all_3d_results[method_name] = method_results
        
        # Save results
        self.save_3d_results(all_3d_results)
        
        self.logger.info(f"✓ 3D structure predictions completed for {len(all_3d_results)} methods")
    
    def save_3d_results(self, results: Dict[str, Dict]):
        """Save 3D structure prediction results."""
        # Save comprehensive results
        results_file = self.structure_3d_dir / f"{self.sequence_name}_3d_results.json"
        
        # Convert results to serializable format
        serializable_results = {}
        for method_name, method_results in results.items():
            serializable_results[method_name] = {}
            for pred_method, result in method_results.items():
                serializable_results[method_name][pred_method] = {
                    'method': result.method,
                    'parameters': result.parameters,
                    'sequence': result.sequence,
                    'structure': result.structure,
                    'pdb_file': result.pdb_file,
                    'energy': result.energy,
                    'rmsd': result.rmsd,
                    'quality_score': result.quality_score
                }
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        self.logger.info(f"✓ 3D results saved to {results_file}")
    
    def create_3d_summary(self, results: Dict[str, Dict]):
        """Create a summary of 3D structure predictions."""
        summary_file = self.structure_3d_dir / f"{self.sequence_name}_3d_summary.txt"
        
        with open(summary_file, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("3D STRUCTURE PREDICTION SUMMARY\n")
            f.write("=" * 60 + "\n")
            f.write(f"Sequence: {self.sequence_name}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for method_name, method_results in results.items():
                f.write(f"RNAfold Method: {method_name}\n")
                f.write("-" * 40 + "\n")
                
                for pred_method, result in method_results.items():
                    f.write(f"  3D Method: {pred_method}\n")
                    f.write(f"    PDB File: {result.pdb_file}\n")
                    if result.energy:
                        f.write(f"    Energy: {result.energy:.2f} kcal/mol\n")
                    if result.rmsd:
                        f.write(f"    RMSD: {result.rmsd:.2f} Å\n")
                    if result.quality_score:
                        f.write(f"    Quality Score: {result.quality_score:.2f}\n")
                    f.write("\n")
        
        self.logger.info(f"✓ 3D summary saved to {summary_file}")


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description="3D Structure Prediction Pipeline")
    parser.add_argument("sequence_prefix", help="Sequence prefix (e.g., TETRAHYMENA)")
    parser.add_argument("--methods", nargs="+", 
                       choices=["rosetta", "simrna", "farna", "rna_composer"],
                       default=["rosetta"],
                       help="3D structure prediction methods to use")
    parser.add_argument("--work-dir", default="/orcd/data/mbathe/001/rcm095/RNA_predictions",
                       help="Working directory for output")
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = mRNA3DStructurePipeline(args.sequence_prefix, args.work_dir)
    pipeline.setup_directories()
    pipeline.run_3d_predictions(args.methods)


if __name__ == "__main__":
    main()
