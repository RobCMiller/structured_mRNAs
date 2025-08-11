#!/bin/bash
#SBATCH -J rosetta_build
#SBATCH -o rosetta_build.%j.output
#SBATCH -e rosetta_build.%j.error
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

# Set working directory - build in /nobackup where git works reliably
cd /nobackup/users/rcm095/Code/rosetta_build

echo "Starting ROSETTA build at $(date)"
echo "Working directory: $(pwd)"
echo "Available resources: 1 GPU, 256GB RAM"

# Check if we have the source files
echo "Checking source directory..."
ls -la source/

# Check if scons.py exists
if [ -f "source/scons.py" ]; then
    echo "Found scons.py, proceeding with build..."
    
    # Change to source directory and build
    cd source
    
    # Build ROSETTA with RNA protocols
    echo "Building ROSETTA with RNA protocols..."
    python scons.py -j 80 mode=release bin
    # Note: -j 80 for 80 threads, mode=release for optimized build, bin to build executables
    
    echo "Build completed at $(date)"
    
    # Check if executables were created
    if [ -d "build/release/bin" ]; then
        echo "Build directory created. Checking for executables..."
        ls -la build/release/bin/ | grep rna_denovo
        
        # Copy executables to processing directory for easy access
        echo "Copying executables to processing directory..."
        mkdir -p /orcd/data/mbathe/001/rcm095/rosetta_binaries
        cp build/release/bin/rna_denovo* /orcd/data/mbathe/001/rcm095/rosetta_binaries/
        echo "Executables copied to /orcd/data/mbathe/001/rcm095/rosetta_binaries/"
    else
        echo "Build directory not found. Build may have failed."
    fi
    
else
    echo "ERROR: scons.py not found in source directory!"
    echo "Available files in source:"
    ls -la
    exit 1
fi

echo "ROSETTA build script completed at $(date)"
