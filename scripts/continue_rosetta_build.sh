#!/bin/bash
#SBATCH -J rosetta_continue
#SBATCH -o %x.%j.output
#SBATCH -e %x.%j.error
#SBATCH --mail-user=rcm095@mit.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --mem=256000
#SBATCH --gres=gpu:1
#SBATCH --gpus-per-node=1
#SBATCH --time=10:00:00
#SBATCH -p sched_mit_mbathe
#SBATCH --exclude=node2034

# Load conda and activate environment
source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction

# Set working directory
cd /nobackup/users/rcm095/Code/rosetta_build/source

echo "=== CONTINUING ROSETTA BUILD ==="
echo "Start time: $(date)"
echo "Working directory: $(pwd)"
echo "Conda environment: $CONDA_DEFAULT_ENV"
echo "=================================="

# Remove the corrupted object file
echo "Removing corrupted object file..."
rm -f build/src/release/linux/4.18/64/x86/gcc/8/default/core/init/score_function_corrections.os

# Continue the build from where we left off
echo "Continuing build with 80 threads..."
./scons.py -j80 mode=release bin

# Check build result
if [ $? -eq 0 ]; then
    echo "=== BUILD SUCCESSFUL ==="
    echo "Checking for executables..."
    ls -la bin/ 2>/dev/null || echo "bin directory not found"
    find . -name "rna_denovo*" -type f -executable 2>/dev/null || echo "No rna_denovo executables found"
else
    echo "=== BUILD FAILED ==="
    echo "Exit code: $?"
fi

echo "=== BUILD COMPLETED ==="
echo "End time: $(date)"
