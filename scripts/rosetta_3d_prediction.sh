#!/bin/bash
#SBATCH -J rosetta_3d_pred
#SBATCH -o %x.%j.output
#SBATCH -e %x.%j.error
#SBATCH --mail-user=rcm095@mit.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --mem=64000
#SBATCH --time=4:00:00
#SBATCH -p sched_mit_mbathe
#SBATCH --exclude=node2034

# Load conda and activate environment
source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction

# Set working directory
cd /orcd/data/mbathe/001/rcm095/RNA_predictions

echo "=== ROSETTA 3D STRUCTURE PREDICTION ==="
echo "Start time: $(date)"
echo "Working directory: $(pwd)"
echo "Conda environment: $CONDA_DEFAULT_ENV"
echo "======================================"

# Create output directory for ROSETTA results
mkdir -p 3d_structures/rosetta/output/tetrahymena_test

# Run ROSETTA 3D structure prediction
echo "Running ROSETTA rna_denovo on TETRAHYMENA sequence..."
/nobackup/users/rcm095/Code/rosetta_build/source/bin/rna_denovo.linuxgccrelease \
    -sequence "ggcaggaaaccggugaguagcgcaggguucgguguaguccgugaggcgaaagcgcuagccgaaaggcgaaaccgcugaugaguagcgcaggguucgauccgguagcgaaagcgcuagccgaaaggcgaaaccgcu" \
    -nstruct 5 \
    -minimize_rna \
    -out:file:silent 3d_structures/rosetta/output/tetrahymena_test/tetrahymena_3d.out

# Check results
echo "=== PREDICTION COMPLETED ==="
echo "Checking output files..."
ls -la 3d_structures/rosetta/output/tetrahymena_test/

# Convert silent file to PDB if successful
if [ -f "3d_structures/rosetta/output/tetrahymena_test/tetrahymena_3d.out" ]; then
    echo "Converting silent file to PDB..."
    /nobackup/users/rcm095/Code/rosetta_build/source/bin/score_jd2.linuxgccrelease \
        -in:file:silent 3d_structures/rosetta/output/tetrahymena_test/tetrahymena_3d.out \
        -out:file:scorefile 3d_structures/rosetta/output/tetrahymena_test/tetrahymena_3d.fasc \
        -out:file:silent_pdb 3d_structures/rosetta/output/tetrahymena_test/tetrahymena_3d.pdb
fi

echo "=== FINAL STATUS ==="
echo "End time: $(date)"
echo "Output directory: 3d_structures/rosetta/output/tetrahymena_test/"
ls -la 3d_structures/rosetta/output/tetrahymena_test/
