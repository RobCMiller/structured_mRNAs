#!/bin/bash
#SBATCH -J rebuild_rosetta_complete
#SBATCH -o rebuild_rosetta_complete_%j.output
#SBATCH -e rebuild_rosetta_complete_%j.error
#SBATCH --nodes=1
#SBATCH --mem=256000
#SBATCH --gres=gpu:1
#SBATCH --gpus-per-node=1
#SBATCH --time=10:00:00
#SBATCH -p sched_mit_mbathe

# Load environment
source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction

echo "=== Starting complete ROSETTA rebuild ==="
echo "Current directory: $(pwd)"
echo "Conda environment: $CONDA_DEFAULT_ENV"

# Go to parent directory
cd /orcd/data/mbathe/001/rcm095/rosetta_build

# Completely clean everything
echo "=== Cleaning everything ==="
rm -rf rosetta
rm -rf source
rm -rf build
rm -rf tests
rm -rf external

# Re-clone ROSETTA from GitHub
echo "=== Re-cloning ROSETTA from GitHub ==="
git clone https://github.com/RosettaCommons/rosetta.git
cd rosetta

# Initialize and update submodules
echo "=== Initializing submodules ==="
git submodule update --init --recursive

# Go to source directory
cd source

# Clean any previous build artifacts
echo "=== Cleaning build directory ==="
rm -rf build/

# Build ROSETTA with system GCC 8.3.0
echo "=== Building ROSETTA with system GCC 8.3.0 ==="
python3 scons.py -j 80 mode=release bin

echo "=== Build completed! ==="
echo "Checking for executables..."

# Verify the build
if [ -d "build/release/bin" ]; then
    echo "Build directory structure:"
    ls -la build/release/bin/
    
    echo "Checking for rna_denovo:"
    ls -la build/release/bin/rna_denovo*
    
    echo "Checking symlinks:"
    ls -la bin/rna_denovo*
else
    echo "ERROR: Build directory structure is incomplete!"
    echo "Contents of build/:"
    ls -la build/
fi

echo "=== ROSETTA rebuild process completed ==="
