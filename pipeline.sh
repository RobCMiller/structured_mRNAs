#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# RNA 3D Prediction Pipeline (RNAfold → DL models → PaxNet (opt) → ROSETTA)
# ============================================================================
# 
# Usage:
#   ./pipeline.sh MODE FASTA_PATH
#     MODE ∈ {accurate, fast}
# Example:
#   ./pipeline.sh accurate data/seqs/yeast_eEF1A.fasta
# ============================================================================

MODE="${1:-}"
FASTA="${2:-}"

if [[ -z "$MODE" || -z "$FASTA" ]]; then
  echo "Usage: $0 {accurate|fast} path/to/seq.fasta" >&2
  echo "" >&2
  echo "Modes:" >&2
  echo "  accurate: RNAfold → (trRosettaRNA + DeepFoldRNA + NuFold) → PaxNet → ROSETTA" >&2
  echo "  fast:     RNAfold → (RhoFold+ OR RNA-RM) → [PaxNet if ≤ threshold] → ROSETTA" >&2
  exit 1
fi

if [[ ! -f "$FASTA" ]]; then
  echo "Error: FASTA file not found: $FASTA" >&2
  exit 1
fi

# ============================================================================
# CONFIGURATION LOADING
# ============================================================================

# Load config.yaml into env vars (simple parser; no external deps)
cfg_get() { 
  grep -E "^$1:" config.yaml | sed -E "s/^$1:[[:space:]]*//" | tr -d '"'
}

# Load all configuration values
ROSETTA_BIN="$(cfg_get rosetta_bin)"
RNAFOLD_BIN="$(cfg_get rnafold_bin)"
TRR_BIN="$(cfg_get trrosettarna_bin)"
DFR_BIN="$(cfg_get deepfoldrna_bin)"
NUFOLD_BIN="$(cfg_get nufold_bin)"
RHF_BIN="$(cfg_get rhofoldplus_bin)"
RNARM_BIN="$(cfg_get rna_rm_bin)"
PAXNET_BIN="$(cfg_get paxnet_bin)"

MAX_MODELS_PER_TOOL="$(cfg_get max_models_per_tool)"
ROSETTA_RELAX_ROUNDS="$(cfg_get rosetta_relax_rounds)"
PAXNET_BATCH_LIMIT="$(cfg_get paxnet_batch_limit)"
ROSETTA_THREADS="$(cfg_get rosetta_threads)"
SLURM_PARTITION="$(cfg_get slurm_partition)"
SLURM_MEMORY="$(cfg_get slurm_memory)"
SLURM_TIME="$(cfg_get slurm_time)"
SLURM_CPUS="$(cfg_get slurm_cpus)"

# ============================================================================
# VALIDATION AND SETUP
# ============================================================================

# Validate required tools
if [[ ! -x "$RNAFOLD_BIN" ]]; then 
  echo "Error: RNAfold not found: $RNAFOLD_BIN" >&2
  exit 2
fi

if [[ ! -d "$ROSETTA_BIN" ]]; then 
  echo "Error: ROSETTA bin directory not found: $ROSETTA_BIN" >&2
  exit 2
fi

# Extract sequence ID and setup working directory
seq_id="$(basename "${FASTA%.*}")"
root="$(pwd)"
work="$root/work/$seq_id"
mkdir -p "$work/00_rnafold" "$work/10_dl_models" "$work/20_paxnet" "$work/30_rosetta" "logs"

# Setup logging
log() { 
  echo "[$(date +'%F %T')] $*" | tee -a "logs/$seq_id.log"
}

log "=== RNA 3D PREDICTION PIPELINE STARTED ==="
log "Mode: $MODE"
log "Sequence: $seq_id"
log "Working directory: $work"

# ============================================================================
# STEP 0: RNAFOLD SECONDARY STRUCTURE PREDICTION
# ============================================================================

if [[ ! -f "$work/00_rnafold/${seq_id}.ss" ]]; then
  log "Step 0: Running RNAfold secondary structure prediction..."
  "$RNAFOLD_BIN" --noPS <(grep -v '^>' "$FASTA" | tr -d '\n') | \
    awk 'NR==1{print $0} NR==2{print $1}' > "$work/00_rnafold/${seq_id}.ss"
  
  # Extract sequence and secondary structure
  sequence=$(head -1 "$work/00_rnafold/${seq_id}.ss")
  secstruct=$(tail -1 "$work/00_rnafold/${seq_id}.ss")
  
  log "Sequence: ${sequence:0:50}..."
  log "Secondary structure: ${secstruct:0:50}..."
else
  log "Step 0: RNAfold results found, skipping..."
  sequence=$(head -1 "$work/00_rnafold/${seq_id}.ss")
  secstruct=$(tail -1 "$work/00_rnafold/${seq_id}.ss")
fi

# ============================================================================
# STEP 1: DEEP LEARNING MODEL PREDICTIONS
# ============================================================================

log "Step 1: Running deep learning model predictions..."

# Function to run DL model
run_dl_model() {
  local model_name="$1"
  local model_bin="$2"
  local output_dir="$work/10_dl_models/$model_name"
  
  if [[ -z "$model_bin" || "$model_bin" == "/opt/$model_name/bin/$model_name" ]]; then
    log "  $model_name: Not configured, skipping..."
    return 0
  fi
  
  if [[ ! -x "$model_bin" ]]; then
    log "  $model_name: Binary not found, skipping..."
    return 0
  fi
  
  mkdir -p "$output_dir"
  
  if [[ ! -f "$output_dir/${seq_id}_${model_name}.pdb" ]]; then
    log "  $model_name: Running prediction..."
    
    case "$model_name" in
      "trRosettaRNA")
        "$model_bin" -i "$FASTA" -o "$output_dir/${seq_id}_${model_name}.pdb" &
        ;;
      "DeepFoldRNA")
        "$model_bin" --input "$FASTA" --output "$output_dir/${seq_id}_${model_name}.pdb" &
        ;;
      "NuFold")
        python3 "$model_bin" --input "$FASTA" --output "$output_dir/${seq_id}_${model_name}.pdb" &
        ;;
      "RhoFoldPlus")
        python3 "$model_bin" --input "$FASTA" --output "$output_dir/${seq_id}_${model_name}.pdb" &
        ;;
      "RNA_RM")
        python3 "$model_bin" --input "$FASTA" --output "$output_dir/${seq_id}_${model_name}.pdb" &
        ;;
      *)
        log "  $model_name: Unknown model type, skipping..."
        return 0
        ;;
    esac
    
    local pid=$!
    log "  $model_name: Started (PID: $pid)"
  else
    log "  $model_name: Output found, skipping..."
  fi
}

# Run models based on mode
if [[ "$MODE" == "accurate" ]]; then
  log "  Accurate mode: Running trRosettaRNA, DeepFoldRNA, and NuFold..."
  run_dl_model "trRosettaRNA" "$TRR_BIN"
  run_dl_model "DeepFoldRNA" "$DFR_BIN"
  run_dl_model "NuFold" "$NUFOLD_BIN"
elif [[ "$MODE" == "fast" ]]; then
  log "  Fast mode: Running RhoFoldPlus or RNA-RM..."
  if [[ -n "$RHF_BIN" && -x "$RHF_BIN" ]]; then
    run_dl_model "RhoFoldPlus" "$RHF_BIN"
  elif [[ -n "$RNARM_BIN" && -x "$RNARM_BIN" ]]; then
    run_dl_model "RNA_RM" "$RNARM_BIN"
  else
    log "  Warning: Neither RhoFoldPlus nor RNA-RM available for fast mode"
  fi
else
  log "Error: Unknown mode: $MODE" >&2
  exit 1
fi

# Wait for all DL models to complete
log "  Waiting for deep learning models to complete..."
wait

# ============================================================================
# STEP 2: PAXNET MODEL RANKING (OPTIONAL)
# ============================================================================

log "Step 2: Running PaxNet model ranking..."

# Count total models generated
total_models=$(find "$work/10_dl_models" -name "*.pdb" 2>/dev/null | wc -l)
log "  Total models generated: $total_models"

if [[ "$total_models" -gt 0 && -n "$PAXNET_BIN" && -x "$PAXNET_BIN" ]]; then
  if [[ "$total_models" -le "$PAXNET_BATCH_LIMIT" ]]; then
    log "  Running PaxNet ranking on $total_models models..."
    mkdir -p "$work/20_paxnet"
    
    # Collect all PDB files
    find "$work/10_dl_models" -name "*.pdb" > "$work/20_paxnet/models_list.txt"
    
    # Run PaxNet
    python3 "$PAXNET_BIN" \
      --input_list "$work/20_paxnet/models_list.txt" \
      --output "$work/20_paxnet/${seq_id}_paxnet_scores.csv" &
    
    local paxnet_pid=$!
    log "  PaxNet started (PID: $paxnet_pid)"
    wait $paxnet_pid
    
    log "  PaxNet completed, scores saved to $work/20_paxnet/${seq_id}_paxnet_scores.csv"
  else
    log "  Skipping PaxNet: $total_models models exceeds threshold $PAXNET_BATCH_LIMIT"
  fi
else
  log "  PaxNet not available or no models generated, skipping..."
fi

# ============================================================================
# STEP 3: ROSETTA REFINEMENT
# ============================================================================

log "Step 3: Running ROSETTA refinement..."

mkdir -p "$work/30_rosetta"

# Function to submit ROSETTA job
submit_rosetta_job() {
  local model_file="$1"
  local model_name=$(basename "${model_file%.*}")
  local output_file="$work/30_rosetta/${model_name}_rosetta_refined.pdb"
  
  if [[ ! -f "$output_file" ]]; then
    log "  Submitting ROSETTA job for $model_name..."
    
    # Create SLURM script for this model
    cat > "$work/30_rosetta/${model_name}_rosetta.sh" << EOF
#!/bin/bash
#SBATCH -J rosetta_refine_${model_name}
#SBATCH -o %x.%j.output
#SBATCH -e %x.%j.error
#SBATCH -p $SLURM_PARTITION
#SBATCH --mem=$SLURM_MEMORY
#SBATCH -t $SLURM_TIME
#SBATCH -c $SLURM_CPUS

cd "$work/30_rosetta"

# Load conda environment
source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction

# Run ROSETTA refinement
"$ROSETTA_BIN/rna_minimize.linuxgccrelease" \\
  -s "$model_file" \\
  -secstruct "$secstruct" \\
  -nstruct 1 \\
  -minimize_rna \\
  -out:file:silent "${model_name}_rosetta.out" \\
  -out:file:scorefile "${model_name}_rosetta.sc"

# Extract PDB
"$ROSETTA_BIN/extract_pdbs.linuxgccrelease" \\
  -in:file:silent "${model_name}_rosetta.out" \\
  -out:file:silent "${model_name}_rosetta_refined.pdb"

echo "ROSETTA refinement completed for $model_name"
EOF

    # Submit job
    sbatch "$work/30_rosetta/${model_name}_rosetta.sh"
    log "  ROSETTA job submitted for $model_name"
  else
    log "  ROSETTA output found for $model_name, skipping..."
  fi
}

# Submit ROSETTA jobs for all models
if [[ "$total_models" -gt 0 ]]; then
  log "  Submitting ROSETTA refinement jobs for $total_models models..."
  
  # Get list of models (use PaxNet ranking if available)
  if [[ -f "$work/20_paxnet/${seq_id}_paxnet_scores.csv" ]]; then
    log "  Using PaxNet ranking for model selection..."
    # Sort by PaxNet score and take top models
    head -"$MAX_MODELS_PER_TOOL" "$work/20_paxnet/${seq_id}_paxnet_scores.csv" | \
      cut -d',' -f1 | while read model_file; do
      submit_rosetta_job "$model_file"
    done
  else
    log "  No PaxNet ranking, processing all models..."
    find "$work/10_dl_models" -name "*.pdb" | head -"$MAX_MODELS_PER_TOOL" | \
      while read model_file; do
      submit_rosetta_job "$model_file"
    done
  fi
else
  log "  No models to refine with ROSETTA"
fi

# ============================================================================
# COMPLETION
# ============================================================================

log "=== PIPELINE COMPLETED ==="
log "Results available in: $work"
log "Check SLURM queue for ROSETTA jobs: squeue -u \$USER"
log "Log file: logs/$seq_id.log"

echo ""
echo "Pipeline completed successfully!"
echo "Results: $work"
echo "Log: logs/$seq_id.log"
echo ""
echo "Next steps:"
echo "1. Monitor ROSETTA jobs: squeue -u \$USER"
echo "2. Check results in: $work/30_rosetta/"
echo "3. Analyze structures with molecular visualization tools"
