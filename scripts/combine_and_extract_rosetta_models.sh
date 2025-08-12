#!/bin/bash
#SBATCH -J combine_extract_rosetta
#SBATCH -p sched_mit_mbathe
#SBATCH -c 12
#SBATCH -t 01:00:00
#SBATCH --mem=8G
#SBATCH -o combine_extract_rosetta.%j.output
#SBATCH -e combine_extract_rosetta.%j.error

# Combine and extract ROSETTA models from integrated pipeline
# This script combines all 7 silent files and extracts PDB files for all models

source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction

# Set working directory
WORK_DIR="/orcd/data/mbathe/001/rcm095/RNA_predictions"
RESULTS_DIR="$WORK_DIR/results/20250811_19_33_34_RNAfold_Rosetta_results"
ROSETTA_DIR="$RESULTS_DIR/rosetta"
OUTPUT_DIR="$RESULTS_DIR/pdbs"

cd "$WORK_DIR"

echo "=== ROSETTA Model Combination and PDB Extraction ==="
echo "Working directory: $(pwd)"
echo "Results directory: $RESULTS_DIR"
echo "ROSETTA directory: $ROSETTA_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Create output directory for PDB files (already exists, but ensure it's there)
mkdir -p "$OUTPUT_DIR"

# Check if all 7 silent files exist
echo "Checking for ROSETTA silent files..."
for i in {1..7}; do
    if [ $i -eq 1 ]; then
        FILE="$ROSETTA_DIR/model_1_sequence_only.out"
    elif [ $i -eq 2 ]; then
        FILE="$ROSETTA_DIR/model_2_with_secstruct.out"
    else
        FILE="$ROSETTA_DIR/model_${i}_with_secstruct_seed$((i-1)).out"
    fi
    
    if [ -f "$FILE" ]; then
        echo "✓ Found: $FILE"
    else
        echo "✗ Missing: $FILE"
        exit 1
    fi
done

echo ""
echo "All 7 silent files found. Proceeding with combination and extraction..."

# Create a combined silent file
COMBINED_SILENT="$OUTPUT_DIR/combined_models.out"
echo "Creating combined silent file: $COMBINED_SILENT"

# Copy the first file
cp "$ROSETTA_DIR/model_1_sequence_only.out" "$COMBINED_SILENT"

# Append the remaining files (skip the header lines)
for i in {2..7}; do
    if [ $i -eq 2 ]; then
        FILE="$ROSETTA_DIR/model_2_with_secstruct.out"
    else
        FILE="$ROSETTA_DIR/model_${i}_with_secstruct_seed$((i-1)).out"
    fi
    echo "Appending: $FILE"
    
    # Skip the first few lines (header) and append the model data
    tail -n +3 "$FILE" >> "$COMBINED_SILENT"
done

echo "Combined silent file created: $COMBINED_SILENT"
echo "File size: $(du -h "$COMBINED_SILENT" | cut -f1)"

# Extract PDB files from the combined silent file
echo ""
echo "Extracting PDB files from combined silent file..."
cd "$OUTPUT_DIR"

/nobackup/users/rcm095/Code/rosetta_build/source/bin/extract_pdbs.linuxgccrelease \
    -in:file:silent combined_models.out \
    -in:file:silent_struct_type rna

# Check what PDB files were created
echo ""
echo "PDB files created:"
ls -la S_*.pdb 2>/dev/null || echo "No PDB files found"

# Count PDB files
PDB_COUNT=$(ls S_*.pdb 2>/dev/null | wc -l)
echo "Total PDB files: $PDB_COUNT"

# Create a summary report
echo ""
echo "=== EXTRACTION SUMMARY ==="
echo "Combined silent file: $COMBINED_SILENT"
echo "PDB files created: $PDB_COUNT"
echo "Output directory: $OUTPUT_DIR"
echo ""

if [ $PDB_COUNT -eq 7 ]; then
    echo "✓ SUCCESS: All 7 models extracted to PDB format"
    echo "Models: S_000001.pdb through S_000007.pdb"
else
    echo "⚠ WARNING: Expected 7 PDB files, got $PDB_COUNT"
fi

echo ""
echo "=== FINAL STATUS ==="
echo "End time: $(date)"
echo "Results directory: $RESULTS_DIR"
echo "Combined PDBs: $OUTPUT_DIR"
