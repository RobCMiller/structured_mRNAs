#!/bin/bash
#SBATCH --mail-user=rcm095@mit.edu
#SBATCH --mail-type=ALL
#SBATCH -N 1
#SBATCH -n 8                 # 8 MPI ranks
#SBATCH --cpus-per-task=10   # 10 OpenMP threads per rank
#SBATCH --mem=128000
#SBATCH --gres=gpu:2
#SBATCH -p sched_cdrennan
#SBATCH --exclude=node2021
#SBATCH --time=48:00:00
#SBATCH -J 3d_structure_prediction
#SBATCH -o 3d_structure_prediction.%j.out
#SBATCH -e 3d_structure_prediction.%j.err

# Load environment
source /nobackup/users/jhdavis/cd_software/miniconda3/etc/profile.d/conda.sh
conda activate rna_prediction

# Set working directory
cd /orcd/data/mbathe/001/rcm095/RNA_predictions

# Run 3D structure predictions for TETRAHYMENA
echo "Starting 3D structure predictions for TETRAHYMENA..."
echo "Available resources: 2 GPUs, 80 CPUs (8 ranks × 10 threads)"
echo "Methods: rosetta, simrna, farna, rna_composer"

# Run the 3D structure pipeline
python scripts/mrna_3d_structure_pipeline.py TETRAHYMENA --methods rosetta simrna farna rna_composer

echo "3D structure predictions completed!"
