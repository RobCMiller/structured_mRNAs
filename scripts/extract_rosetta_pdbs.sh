#!/bin/bash
#SBATCH -J rosetta_extract_pdbs
#SBATCH -o %x.%j.output
#SBATCH -e %x.%j.error
#SBATCH --mail-user=rcm095@mit.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --mem=16000
#SBATCH --time=1:00:00
#SBATCH -p sched_mit_mbathe
#SBATCH --exclude=node2034

# Load conda and activate environment
source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction

# Set working directory
cd /orcd/data/mbathe/001/rcm095/RNA_predictions/3d_structures/rosetta/output/tetrahymena_test

echo "=== EXTRACTING ROSETTA PDB FILES ==="
echo "Start time: $(date)"
echo "Working directory: $(pwd)"
echo "Conda environment: $CONDA_DEFAULT_ENV"
echo "==================================="

# Extract PDB files from silent file
echo "Extracting PDB files from tetrahymena_3d.out..."
/nobackup/users/rcm095/Code/rosetta_build/source/bin/extract_pdbs.linuxgccrelease \
    -in:file:silent tetrahymena_3d.out \
    -in:file:silent_struct_type rna

# Check results
echo "=== EXTRACTION COMPLETED ==="
echo "Checking extracted files..."
ls -la *.pdb 2>/dev/null || echo "No PDB files found"

echo "=== FINAL STATUS ==="
echo "End time: $(date)"
echo "Output directory: $(pwd)"
ls -la
