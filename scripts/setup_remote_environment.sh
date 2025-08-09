#!/bin/bash
# Setup script for RNA prediction environment on satori

echo "=== Setting up RNA Prediction Environment on Satori ==="

# Set the working directory
RNA_DIR="/orcd/data/mbathe/001/rcm095/RNA_predictions"
cd $RNA_DIR

echo "Working directory: $RNA_DIR"

# Create directory structure
mkdir -p $RNA_DIR/{src,config,scripts,data,output,temp,logs}
echo "✓ Created directory structure"

# Copy pipeline files to remote server
echo "Copying pipeline files to remote server..."

# Create a temporary script to copy files
cat > /tmp/copy_pipeline.sh << 'EOF'
#!/bin/bash
RNA_DIR="/orcd/data/mbathe/001/rcm095/RNA_predictions"

# Copy source files
scp -r src/* satori:$RNA_DIR/src/
scp -r config/* satori:$RNA_DIR/config/
scp -r scripts/* satori:$RNA_DIR/scripts/
scp requirements.txt satori:$RNA_DIR/
scp README.md satori:$RNA_DIR/

echo "✓ Files copied to remote server"
EOF

chmod +x /tmp/copy_pipeline.sh
/tmp/copy_pipeline.sh

# Set up conda environment on remote server
echo "Setting up conda environment..."

ssh satori << 'EOF'
RNA_DIR="/orcd/data/mbathe/001/rcm095/RNA_predictions"
cd $RNA_DIR

# Source conda
source /nobackup/users/jhdavis/cd_software/miniconda3/etc/profile.d/conda.sh

# Create new conda environment for RNA prediction
conda create -n rna_prediction python=3.9 -y
conda activate rna_prediction

# Install required packages
conda install -c conda-forge -c bioconda \
    numpy scipy pandas matplotlib seaborn \
    biopython pyyaml click tqdm loguru pytest \
    viennarna -y

# Install additional packages via pip
pip install requests

echo "✓ Conda environment 'rna_prediction' created and packages installed"

# Create activation script
cat > $RNA_DIR/activate_rna_env.sh << 'ENV_SCRIPT'
#!/bin/bash
# Activation script for RNA prediction environment
export RNA_DIR="/orcd/data/mbathe/001/rcm095/RNA_predictions"
cd $RNA_DIR
source /nobackup/users/jhdavis/cd_software/miniconda3/etc/profile.d/conda.sh
conda activate rna_prediction
export PYTHONPATH="$RNA_DIR:$PYTHONPATH"
echo "✓ RNA prediction environment activated"
echo "Working directory: $RNA_DIR"
ENV_SCRIPT

chmod +x $RNA_DIR/activate_rna_env.sh

# Test RNAfold installation
echo "Testing RNAfold installation..."
RNAfold --version
if [ $? -eq 0 ]; then
    echo "✓ RNAfold is working"
else
    echo "✗ RNAfold not found or not working"
fi

EOF

echo "=== Remote Environment Setup Complete ==="
echo ""
echo "To activate the environment on satori:"
echo "  ssh satori"
echo "  source /orcd/data/mbathe/001/rcm095/RNA_predictions/activate_rna_env.sh"
echo ""
echo "To test the pipeline:"
echo "  python scripts/mrna_structure_pipeline.py TETRAHYMENA"
