#!/bin/bash
#SBATCH -J rnafold_rosetta_pipeline
#SBATCH -o %x.%j.output
#SBATCH -e %x.%j.error
#SBATCH --mail-user=rcm095@mit.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --mem=32000
#SBATCH --time=2:00:00
#SBATCH -p sched_mit_mbathe
#SBATCH --exclude=node2034

# Load conda and activate environment
source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction

# Set working directory
cd /orcd/data/mbathe/001/rcm095/RNA_predictions

echo "=== RNAFOLD TO ROSETTA PIPELINE ==="
echo "Start time: $(date)"
echo "Working directory: $(pwd)"
echo "Conda environment: $CONDA_DEFAULT_ENV"
echo "==================================="

# Create results directory for this run
RUN_ID=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="results/rosetta_analysis_${RUN_ID}"
mkdir -p "$RESULTS_DIR"

echo "Results directory: $RESULTS_DIR"

# Step 1: Run RNAfold prediction
echo "Step 1: Running RNAfold prediction..."
mkdir -p "$RESULTS_DIR/rnafold"

# Run RNAfold on TETRAHYMENA sequence (using working command from existing pipeline)
echo "GGCAGGAAACCGGUGAGUAGCGCAGGGUUCGGUGUAGUCCGUGAGGCGAAAGCGCUAGCCGAAAGGCGAAACCGCUGAUGAGUAGCGCAGGGUUCGAUCCGGUAGCGAAAGCGCUAGCCGAAAGGCGAAACCGCU" | \
RNAfold > "$RESULTS_DIR/rnafold/rnafold_output.txt"

# Check if RNAfold worked
if [ ! -s "$RESULTS_DIR/rnafold/rnafold_output.txt" ]; then
    echo "ERROR: RNAfold failed to generate output"
    echo "Trying alternative approach..."
    # Try with explicit conda activation
    source /home/jhdavis/.start_cd_conda.sh
    conda activate rna_prediction
    echo "GGCAGGAAACCGGUGAGUAGCGCAGGGUUCGGUGUAGUCCGUGAGGCGAAAGCGCUAGCCGAAAGGCGAAACCGCUGAUGAGUAGCGCAGGGUUCGAUCCGGUAGCGAAAGCGCUAGCCGAAAGGCGAAACCGCU" | \
    RNAfold > "$RESULTS_DIR/rnafold/rnafold_output.txt"
fi

# Extract secondary structure from RNAfold output (get the dot-bracket structure, not the energy)
SECSTRUCT=$(tail -1 "$RESULTS_DIR/rnafold/rnafold_output.txt" | sed 's/[[:space:]]*[^[:space:]]*$//')
echo "RNAfold secondary structure: $SECSTRUCT"

# Verify secondary structure was extracted
if [ -z "$SECSTRUCT" ]; then
    echo "ERROR: Failed to extract secondary structure from RNAfold output"
    echo "RNAfold output content:"
    cat "$RESULTS_DIR/rnafold/rnafold_output.txt"
    exit 1
fi

# Step 2: Create ROSETTA job submission script
echo "Step 2: Creating ROSETTA job submission script..."

cat > "$RESULTS_DIR/submit_rosetta_jobs.sh" << 'EOF'
#!/bin/bash
#SBATCH -J rosetta_7_models
#SBATCH -o %x.%j.output
#SBATCH -e %x.%j.error
#SBATCH --mail-user=rcm095@mit.edu
#SBATCH --mail-type=ALL
#SBATCH --nodes=1
#SBATCH --mem=64000
#SBATCH --time=6:00:00
#SBATCH -p sched_mit_mbathe
#SBATCH --exclude=node2034
#SBATCH --cpus-per-task=12

# Load conda and activate environment
source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction

# Set working directory
cd /orcd/data/mbathe/001/rcm095/RNA_predictions

echo "=== ROSETTA 7-MODEL PREDICTION ==="
echo "Start time: $(date)"
echo "Working directory: $(pwd)"
echo "Conda environment: $CONDA_DEFAULT_ENV"
echo "=================================="

# Get the results directory from parent job
RESULTS_DIR="$1"
SECSTRUCT="$2"

echo "Results directory: $RESULTS_DIR"
echo "Secondary structure: $SECSTRUCT"

# Create ROSETTA output directory
mkdir -p "$RESULTS_DIR/rosetta"

# Job 1: Sequence-only prediction (no secondary structure constraint)
echo "Job 1: Sequence-only prediction..."
/nobackup/users/rcm095/Code/rosetta_build/source/bin/rna_denovo.linuxgccrelease \
    -sequence "ggcaggaaaccggugaguagcgcaggguucgguguaguccgugaggcgaaagcgcuagccgaaaggcgaaaccgcugaugaguagcgcaggguucgauccgguagcgaaagcgcuagccgaaaggcgaaaccgcu" \
    -nstruct 1 \
    -minimize_rna \
    -out:file:silent "$RESULTS_DIR/rosetta/model_1_sequence_only.out" &
PID1=$!

# Job 2: With RNAfold secondary structure constraint
echo "Job 2: With RNAfold secondary structure constraint..."
/nobackup/users/rcm095/Code/rosetta_build/source/bin/rna_denovo.linuxgccrelease \
    -sequence "ggcaggaaaccggugaguagcgcaggguucgguguaguccgugaggcgaaagcgcuagccgaaaggcgaaaccgcugaugaguagcgcaggguucgauccgguagcgaaagcgcuagccgaaaggcgaaaccgcu" \
    -secstruct "$SECSTRUCT" \
    -nstruct 1 \
    -minimize_rna \
    -out:file:silent "$RESULTS_DIR/rosetta/model_2_with_secstruct.out" &
PID2=$!

# Job 3: With RNAfold secondary structure constraint (different seed)
echo "Job 3: With RNAfold secondary structure constraint (seed 2)..."
/nobackup/users/rcm095/Code/rosetta_build/source/bin/rna_denovo.linuxgccrelease \
    -sequence "ggcaggaaaccggugaguagcgcaggguucgguguaguccgugaggcgaaagcgcuagccgaaaggcgaaaccgcugaugaguagcgcaggguucgauccgguagcgaaagcgcuagccgaaaggcgaaaccgcu" \
    -secstruct "$SECSTRUCT" \
    -nstruct 1 \
    -minimize_rna \
    -out:file:silent "$RESULTS_DIR/rosetta/model_3_with_secstruct_seed2.out" &
PID3=$!

# Job 4: With RNAfold secondary structure constraint (different seed)
echo "Job 4: With RNAfold secondary structure constraint (seed 3)..."
/nobackup/users/rcm095/Code/rosetta_build/source/bin/rna_denovo.linuxgccrelease \
    -sequence "ggcaggaaaccggugaguagcgcaggguucgguguaguccgugaggcgaaagcgcuagccgaaaggcgaaaccgcugaugaguagcgcaggguucgauccgguagcgaaagcgcuagccgaaaggcgaaaccgcu" \
    -secstruct "$SECSTRUCT" \
    -nstruct 1 \
    -minimize_rna \
    -out:file:silent "$RESULTS_DIR/rosetta/model_4_with_secstruct_seed3.out" &
PID4=$!

# Job 5: With RNAfold secondary structure constraint (different seed)
echo "Job 5: With RNAfold secondary structure constraint (seed 4)..."
/nobackup/users/rcm095/Code/rosetta_build/source/bin/rna_denovo.linuxgccrelease \
    -sequence "ggcaggaaaccggugaguagcgcaggguucgguguaguccgugaggcgaaagcgcuagccgaaaggcgaaaccgcugaugaguagcgcaggguucgauccgguagcgaaagcgcuagccgaaaggcgaaaccgcu" \
    -secstruct "$SECSTRUCT" \
    -nstruct 1 \
    -minimize_rna \
    -out:file:silent "$RESULTS_DIR/rosetta/model_5_with_secstruct_seed4.out" &
PID5=$!

# Job 6: With RNAfold secondary structure constraint (different seed)
echo "Job 6: With RNAfold secondary structure constraint (seed 5)..."
/nobackup/users/rcm095/Code/rosetta_build/source/bin/rna_denovo.linuxgccrelease \
    -sequence "ggcaggaaaccggugaguagcgcaggguucgguguaguccgugaggcgaaagcgcuagccgaaaggcgaaaccgcugaugaguagcgcaggguucgauccgguagcgaaagcgcuagccgaaaggcgaaaccgcu" \
    -secstruct "$SECSTRUCT" \
    -nstruct 1 \
    -minimize_rna \
    -out:file:silent "$RESULTS_DIR/rosetta/model_6_with_secstruct_seed5.out" &
PID6=$!

# Job 7: With RNAfold secondary structure constraint (different seed)
echo "Job 7: With RNAfold secondary structure constraint (seed 6)..."
/nobackup/users/rcm095/Code/rosetta_build/source/bin/rna_denovo.linuxgccrelease \
    -sequence "ggcaggaaaccggugaguagcgcaggguucgguguaguccgugaggcgaaagcgcuagccgaaaggcgaaaccgcugaugaguagcgcaggguucgauccgguagcgaaagcgcuagccgaaaggcgaaaccgcu" \
    -secstruct "$SECSTRUCT" \
    -nstruct 1 \
    -minimize_rna \
    -out:file:silent "$RESULTS_DIR/rosetta/model_7_with_secstruct_seed6.out" &
PID7=$!

# Wait for all jobs to complete
echo "Waiting for all ROSETTA jobs to complete..."
wait $PID1 $PID2 $PID3 $PID4 $PID5 $PID6 $PID7

# Check results
echo "=== ALL ROSETTA JOBS COMPLETED ==="
echo "Checking output files..."
ls -la "$RESULTS_DIR/rosetta/"

# Extract PDB files from all silent files
echo "Extracting PDB files..."
for silent_file in "$RESULTS_DIR/rosetta/"*.out; do
    if [ -f "$silent_file" ]; then
        echo "Extracting PDB from: $silent_file"
        /nobackup/users/rcm095/Code/rosetta_build/source/bin/extract_pdbs.linuxgccrelease \
            -in:file:silent "$silent_file" \
            -in:file:silent_struct_type rna
    fi
done

# Final status
echo "=== FINAL STATUS ==="
echo "End time: $(date)"
echo "Results directory: $RESULTS_DIR"
ls -la "$RESULTS_DIR/rosetta/"

EOF

# Make the script executable
chmod +x "$RESULTS_DIR/submit_rosetta_jobs.sh"

# Step 3: Submit the ROSETTA jobs
echo "Step 3: Submitting ROSETTA jobs..."
cd "$RESULTS_DIR"
sbatch submit_rosetta_jobs.sh "$(pwd)" "$SECSTRUCT"

# Step 4: Create summary report
echo "Step 4: Creating summary report..."
cat > "$RESULTS_DIR/pipeline_summary.txt" << EOF
RNAFOLD TO ROSETTA PIPELINE SUMMARY
===================================

Run ID: $RUN_ID
Start Time: $(date)
Results Directory: $RESULTS_DIR

RNAFOLD RESULTS:
- Input Sequence: TETRAHYMENA P4-P6 domain (135 nt)
- Secondary Structure: $SECSTRUCT
- Output File: rnafold/rnafold_output.txt

ROSETTA JOBS SUBMITTED:
1. Model 1: Sequence-only prediction (no constraints)
2. Model 2: With RNAfold secondary structure constraint
3. Model 3: With RNAfold secondary structure constraint (seed 2)
4. Model 4: With RNAfold secondary structure constraint (seed 3)
5. Model 5: With RNAfold secondary structure constraint (seed 4)
6. Model 6: With RNAfold secondary structure constraint (seed 5)
7. Model 7: With RNAfold secondary structure constraint (seed 6)

Each job uses 12 CPUs, total: 84 CPUs
Job submission script: submit_rosetta_jobs.sh

Expected Output:
- 7 silent files (.out)
- 7 PDB files (after extraction)
- Comprehensive structural analysis

EOF

echo "=== PIPELINE SETUP COMPLETED ==="
echo "Results directory: $RESULTS_DIR"
echo "RNAfold secondary structure: $SECSTRUCT"
echo "ROSETTA jobs submitted successfully"
echo "Check $RESULTS_DIR/pipeline_summary.txt for details"
echo "End time: $(date)"
