#!/bin/bash
#SBATCH -J rosetta_test
#SBATCH -o %x.%j.output
#SBATCH -e %x.%j.error
#SBATCH --mail-user=rcm095@mit.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --mem=32000
#SBATCH --time=1:00:00
#SBATCH -p sched_mit_mbathe
#SBATCH --exclude=node2034

# Load conda and activate environment
source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction

# Load GCC module for compatibility
module load gcc/8.3.0

# Set working directory
cd /nobackup/users/rcm095/Code/rosetta_build/source

echo "=== TESTING ROSETTA ON COMPUTE NODE ==="
echo "Start time: $(date)"
echo "Working directory: $(pwd)"
echo "Conda environment: $CONDA_DEFAULT_ENV"
echo "GCC version: $(gcc --version | head -1)"
echo "======================================"

# Test ROSETTA executable
echo "Testing rna_denovo executable..."
./bin/rna_denovo.linuxgccrelease -help | head -20

echo "=== TEST COMPLETED ==="
echo "End time: $(date)"
