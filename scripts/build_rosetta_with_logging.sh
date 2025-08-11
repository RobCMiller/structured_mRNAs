#!/bin/bash
#SBATCH -J rosetta_build_logged
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

echo "=== ROSETTA BUILD WITH LOGGING ==="
echo "Start time: $(date)"
echo "Working directory: $(pwd)"
echo "Conda environment: $CONDA_DEFAULT_ENV"
echo "=================================="

# Clean up any corrupted gemmi submodule if it exists
if [ -d ".git/modules/source/external/gemmi_repo" ]; then
    echo "Cleaning up corrupted gemmi submodule..."
    rm -rf .git/modules/source/external/gemmi_repo
    rm -rf source/external/gemmi_repo
fi

# Run scons with detailed logging
echo "Starting scons build with 80 threads..."
./scons.py -j80 mode=release bin 2>&1 | tee build.log

# Check build result
if [ $? -eq 0 ]; then
    echo "=== BUILD SUCCESSFUL ==="
    echo "Checking for executables..."
    ls -la bin/ 2>/dev/null || echo "bin directory not found"
    find . -name "rna_denovo*" -type f -executable 2>/dev/null || echo "No rna_denovo executables found"
else
    echo "=== BUILD FAILED ==="
    echo "Exit code: $?"
    echo "Check build.log for details"
fi

echo "=== BUILD COMPLETED ==="
echo "End time: $(date)"
echo "Check build.log for full output"
