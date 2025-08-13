#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# ML Tools Installation Script for Satori Server
# ============================================================================
# 
# This script installs all ML-based RNA prediction tools on Satori.
# Run this on the Satori server after activating the rna_prediction environment.
# ============================================================================

echo "=== ML Tools Installation Script for Satori ==="
echo "This will install RNA structure prediction tools in your rna_prediction environment"
echo ""

# Check if we're in the right environment
if [[ "$CONDA_DEFAULT_ENV" != "rna_prediction" ]]; then
    echo "❌ Error: Please activate the rna_prediction conda environment first:"
    echo "   conda activate rna_prediction"
    exit 1
fi

echo "✅ Conda environment: $CONDA_DEFAULT_ENV"

# Check if we're on Satori
if [[ ! -d "/nobackup/users/rcm095" ]]; then
    echo "❌ Error: This script is designed to run on Satori server"
    exit 1
fi

echo "✅ Running on Satori server"

# Create Code directory if it doesn't exist
CODE_DIR="/nobackup/users/rcm095/Code"
mkdir -p "$CODE_DIR"
cd "$CODE_DIR"

echo ""
echo "=== Phase 1: Installing Core Dependencies ==="

# Install PyTorch with CUDA support
echo "Installing PyTorch with CUDA support..."
conda install -c conda-forge pytorch torchvision torchaudio cudatoolkit=11.3 -y

# Install TensorFlow
echo "Installing TensorFlow..."
conda install -c conda-forge tensorflow-gpu=2.8.0 -y

# Install other dependencies
echo "Installing additional dependencies..."
conda install -c conda-forge openmm pdbfixer biopython -y

echo "✅ Core dependencies installed"

echo ""
echo "=== Phase 2: Installing Individual Tools ==="

# Tool 1: trRosettaRNA
echo ""
echo "Installing trRosettaRNA..."
if [[ ! -d "trRosettaRNA" ]]; then
    git clone https://github.com/THUDM/trRosettaRNA.git
    cd trRosettaRNA
    pip install -e .
    
    # Download pre-trained models
    echo "Downloading trRosettaRNA models..."
    wget https://github.com/THUDM/trRosettaRNA/releases/download/v1.0.0/trRosettaRNA_models.tar.gz
    tar -xzf trRosettaRNA_models.tar.gz
    rm trRosettaRNA_models.tar.gz
    
    cd ..
    echo "✅ trRosettaRNA installed"
else
    echo "✅ trRosettaRNA already exists, skipping..."
fi

# Tool 2: DeepFoldRNA
echo ""
echo "Installing DeepFoldRNA..."
if [[ ! -d "deepfold-rna" ]]; then
    git clone https://github.com/deepmind/deepfold-rna.git
    cd deepfold-rna
    pip install -e .
    cd ..
    echo "✅ DeepFoldRNA installed"
else
    echo "✅ DeepFoldRNA already exists, skipping..."
fi

# Tool 3: NuFold
echo ""
echo "Installing NuFold..."
if [[ ! -d "nufold" ]]; then
    git clone https://github.com/soedinglab/nufold.git
    cd nufold
    pip install -e .
    cd ..
    echo "✅ NuFold installed"
else
    echo "✅ NuFold already exists, skipping..."
fi

# Tool 4: RhoFoldPlus
echo ""
echo "Installing RhoFoldPlus..."
if [[ ! -d "RhoFoldPlus" ]]; then
    git clone https://github.com/RhoFold/RhoFoldPlus.git
    cd RhoFoldPlus
    pip install -e .
    cd ..
    echo "✅ RhoFoldPlus installed"
else
    echo "✅ RhoFoldPlus already exists, skipping..."
fi

# Tool 5: RNA-RM
echo ""
echo "Installing RNA-RM..."
if [[ ! -d "RNA-RM" ]]; then
    git clone https://github.com/RNA-RM/RNA-RM.git
    cd RNA-RM
    pip install -e .
    cd ..
    echo "✅ RNA-RM installed"
else
    echo "✅ RNA-RM already exists, skipping..."
fi

# Tool 6: PaxNet
echo ""
echo "Installing PaxNet..."
if [[ ! -d "PaxNet" ]]; then
    git clone https://github.com/PaxNet/PaxNet.git
    cd PaxNet
    pip install -e .
    cd ..
    echo "✅ PaxNet installed"
else
    echo "✅ PaxNet already exists, skipping..."
fi

echo ""
echo "=== Phase 3: Testing Installation ==="

# Create test script
cat > test_ml_tools.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import sys
import os

tools = [
    ('trRosettaRNA', 'trRosettaRNA -h'),
    ('DeepFoldRNA', 'python -m deepfoldrna --help'),
    ('NuFold', 'python /nobackup/users/rcm095/Code/nufold/run_nufold.py --help'),
    ('RhoFoldPlus', 'python /nobackup/users/rcm095/Code/RhoFoldPlus/run_rhofoldplus.py --help'),
    ('RNA-RM', 'python /nobackup/users/rcm095/Code/RNA-RM/run_rna_rm.py --help'),
    ('PaxNet', 'python /nobackup/users/rcm095/Code/PaxNet/score_models.py --help')
]

print("Testing ML Tool Installation...")
print("=" * 50)

results = {}
for tool_name, test_cmd in tools:
    try:
        result = subprocess.run(test_cmd.split(), capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {tool_name}: INSTALLED")
            results[tool_name] = "INSTALLED"
        else:
            print(f"❌ {tool_name}: FAILED (exit code: {result.returncode})")
            results[tool_name] = "FAILED"
    except FileNotFoundError:
        print(f"❌ {tool_name}: NOT FOUND")
        results[tool_name] = "NOT_FOUND"
    except subprocess.TimeoutExpired:
        print(f"⚠️  {tool_name}: TIMEOUT (may be working but slow)")
        results[tool_name] = "TIMEOUT"
    except Exception as e:
        print(f"❌ {tool_name}: ERROR ({e})")
        results[tool_name] = "ERROR"

print("\n" + "=" * 50)
print("Installation Summary:")
print("=" * 50)

for tool_name, status in results.items():
    print(f"{tool_name:15}: {status}")

# Check CUDA availability
print("\nCUDA Status:")
try:
    import torch
    if torch.cuda.is_available():
        print(f"✅ PyTorch CUDA: Available ({torch.cuda.get_device_name(0)})")
    else:
        print("❌ PyTorch CUDA: Not available")
except ImportError:
    print("❌ PyTorch: Not installed")

try:
    import tensorflow as tf
    if tf.config.list_physical_devices('GPU'):
        print(f"✅ TensorFlow GPU: Available ({len(tf.config.list_physical_devices('GPU'))} devices)")
    else:
        print("❌ TensorFlow GPU: Not available")
except ImportError:
    print("❌ TensorFlow: Not installed")

print("\nInstallation Status Complete!")
EOF

# Run test
echo "Running installation tests..."
python test_ml_tools.py

echo ""
echo "=== Phase 4: Updating Configuration ==="

# Create updated config file
cat > updated_config.yaml << 'EOF'
# RNA 3D Prediction Pipeline Configuration - Updated for Satori ML Tools
# Edit these paths to match your installation

# ============================================================================
# TOOL PATHS (UPDATED FOR SATORI ML TOOLS)
# ============================================================================

# ROSETTA installation
rosetta_bin: "/nobackup/users/rcm095/Code/rosetta_build/source/bin"
rnafold_bin: "/home/jhdavis/miniconda3/envs/rna_prediction/bin/RNAfold"

# Deep Learning Model Paths (Updated for Satori)
trrosettarna_bin: "/nobackup/users/rcm095/Code/trRosettaRNA/bin/trRosettaRNA"
deepfoldrna_bin: "/nobackup/users/rcm095/Code/deepfold-rna/bin/deepfoldrna"
nufold_bin: "/nobackup/users/rcm095/Code/nufold/run_nufold.py"
rhofoldplus_bin: "/nobackup/users/rcm095/Code/RhoFoldPlus/run_rhofoldplus.py"
rna_rm_bin: "/nobackup/users/rcm095/Code/RNA-RM/run_rna_rm.py"
paxnet_bin: "/nobackup/users/rcm095/Code/PaxNet/score_models.py"

# ============================================================================
# PIPELINE TUNABLES (OPTIONAL: adjust based on your needs)
# ============================================================================

# Model Generation Limits
max_models_per_tool: 5          # How many PDBs per DL tool to keep before Rosetta
rosetta_relax_rounds: 2         # How many Rosetta refinement passes
paxnet_batch_limit: 2000        # If total models > this, skip PaxNet by default

# Resource Allocation
rosetta_threads: 8              # Threads per ROSETTA job
max_concurrent_jobs: 4          # Maximum concurrent ROSETTA jobs

# Quality Thresholds
energy_threshold: -50.0          # Energy threshold for keeping models
clash_threshold: 0.3             # Clash score threshold for model filtering

# ============================================================================
# SLURM CONFIGURATION (for cluster execution)
# ============================================================================

# SLURM Parameters
slurm_partition: "sched_mit_mbathe"
slurm_memory: "8G"
slurm_time: "06:00:00"
slurm_cpus: 12

# ============================================================================
# ADVANCED SETTINGS (expert users only)
# ============================================================================

# Model Selection Strategy
use_paxnet_ranking: true        # Enable PaxNet model ranking
use_rosetta_refinement: true    # Enable ROSETTA refinement
use_secondary_constraints: true # Use RNAfold constraints in ROSETTA

# Output Options
save_intermediate_models: true  # Keep intermediate DL model outputs
generate_visualizations: true   # Create structure comparison plots
compress_outputs: false         # Compress large output files

# Debug Options
verbose_logging: true           # Enable detailed logging
save_debug_info: false         # Save intermediate calculation files
EOF

echo "✅ Updated configuration file created: updated_config.yaml"
echo "   Copy this to your project directory and rename to config.yaml"

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "Next steps:"
echo "1. Copy updated_config.yaml to your project directory"
echo "2. Test individual tools with small sequences"
echo "3. Update your pipeline configuration"
echo "4. Test the full pipeline with a single sequence"
echo ""
echo "Tools installed in: $CODE_DIR"
echo "Test results saved in: test_ml_tools.py output above"
