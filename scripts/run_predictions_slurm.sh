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
#SBATCH --time=24:00:00
#SBATCH -J mrna_predictions
#SBATCH -o mrna_predictions.%j.out
#SBATCH -e mrna_predictions.%j.err

# Load required modules
module unload openmpi/3.1.6-cuda-verbs 2>/dev/null
module load spack/20210203 gcc/9.3.0 openmpi/3.1.6-verbs cmake/3.18.4 cuda/11.1.0 fftw/3.3.8

# Set up environment
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

# Set working directory
WORK_DIR="/orcd/data/mbathe/001/rcm095/RNA_predictions"
cd $WORK_DIR

# Activate RNA prediction environment
source /nobackup/users/jhdavis/cd_software/miniconda3/etc/profile.d/conda.sh
conda activate rna_prediction
export PYTHONPATH="$WORK_DIR:$PYTHONPATH"

# Create output directories
mkdir -p $WORK_DIR/output
mkdir -p $WORK_DIR/temp
mkdir -p $WORK_DIR/logs

# Run the prediction pipeline
echo "Starting mRNA structure prediction pipeline..."
echo "Working directory: $WORK_DIR"
echo "Using $SLURM_NTASKS MPI ranks with $SLURM_CPUS_PER_TASK threads each"
echo "GPU devices: $CUDA_VISIBLE_DEVICES"
echo "Python environment: $(which python)"
echo "RNAfold available: $(which RNAfold)"

# Run the main prediction script
python src/main.py \
    --input $WORK_DIR/data/benchmark_data/tetrahymena_p4p6.fasta \
    --output $WORK_DIR/output \
    --config $WORK_DIR/config/pipeline_config.yaml \
    --remote \
    --methods rnafold \
    --log-level INFO

echo "Prediction pipeline completed successfully!"
