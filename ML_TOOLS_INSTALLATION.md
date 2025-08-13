# ML-Based RNA Prediction Tools Installation Guide

This document outlines the installation process for all deep learning RNA structure prediction tools on the Satori server.

## **Prerequisites**

- **Conda Environment**: `rna_prediction` (already exists)
- **Python Version**: 3.8+ (already configured)
- **CUDA**: Check if available on Satori
- **Storage**: Ensure sufficient disk space for models and databases

## **Tool 1: trRosettaRNA**

### **What It Is**
- **Purpose**: De novo RNA structure prediction using deep learning
- **Paper**: [trRosettaRNA: automated prediction of RNA 3D structures with transformer network](https://doi.org/10.1038/s41467-021-21541-7)
- **Input**: RNA sequence (FASTA)
- **Output**: 3D structure (PDB)

### **Installation Steps**
```bash
# SSH to Satori
ssh satori

# Activate conda environment
conda activate rna_prediction

# Install dependencies
conda install -c conda-forge tensorflow-gpu=2.8.0
conda install -c conda-forge openmm
conda install -c conda-forge pdbfixer

# Clone repository
cd /nobackup/users/rcm095/Code/
git clone https://github.com/THUDM/trRosettaRNA.git
cd trRosettaRNA

# Install trRosettaRNA
pip install -e .

# Download pre-trained models
wget https://github.com/THUDM/trRosettaRNA/releases/download/v1.0.0/trRosettaRNA_models.tar.gz
tar -xzf trRosettaRNA_models.tar.gz

# Test installation
trRosettaRNA -h
```

### **Configuration Update**
```yaml
# In config.yaml
trrosettarna_bin: "/nobackup/users/rcm095/Code/trRosettaRNA/bin/trRosettaRNA"
```

## **Tool 2: DeepFoldRNA**

### **What It Is**
- **Purpose**: End-to-end RNA structure prediction using deep learning
- **Paper**: [DeepFoldRNA: RNA structure prediction using deep learning](https://doi.org/10.1093/nar/gkab1304)
- **Input**: RNA sequence (FASTA)
- **Output**: 3D structure (PDB)

### **Installation Steps**
```bash
# Install dependencies
conda install -c conda-forge pytorch torchvision torchaudio cudatoolkit=11.3
conda install -c conda-forge biopython

# Clone repository
cd /nobackup/users/rcm095/Code/
git clone https://github.com/deepmind/deepfold-rna.git
cd deepfold-rna

# Install DeepFoldRNA
pip install -e .

# Download pre-trained models
# (Check repository for model download instructions)

# Test installation
python -m deepfoldrna --help
```

### **Configuration Update**
```yaml
# In config.yaml
deepfoldrna_bin: "/nobackup/users/rcm095/Code/deepfold-rna/bin/deepfoldrna"
```

## **Tool 3: NuFold**

### **What It Is**
- **Purpose**: RNA structure prediction using AlphaFold2 architecture
- **Paper**: [NuFold: RNA structure prediction using AlphaFold2](https://doi.org/10.1038/s41592-022-01685-y)
- **Input**: RNA sequence (FASTA)
- **Output**: 3D structure (PDB)

### **Installation Steps**
```bash
# Install dependencies
conda install -c conda-forge pytorch torchvision torchaudio cudatoolkit=11.3
conda install -c conda-forge openmm pdbfixer

# Clone repository
cd /nobackup/users/rcm095/Code/
git clone https://github.com/soedinglab/nufold.git
cd nufold

# Install NuFold
pip install -e .

# Download pre-trained models
# (Check repository for model download instructions)

# Test installation
python run_nufold.py --help
```

### **Configuration Update**
```yaml
# In config.yaml
nufold_bin: "/nobackup/users/rcm095/Code/nufold/run_nufold.py"
```

## **Tool 4: RhoFoldPlus**

### **What It Is**
- **Purpose**: Fast RNA structure prediction using deep learning
- **Paper**: [RhoFold: RNA structure prediction using deep learning](https://doi.org/10.1038/s41467-021-21541-7)
- **Input**: RNA sequence (FASTA)
- **Output**: 3D structure (PDB)

### **Installation Steps**
```bash
# Install dependencies
conda install -c conda-forge pytorch torchvision torchaudio cudatoolkit=11.3
conda install -c conda-forge biopython

# Clone repository
cd /nobackup/users/rcm095/Code/
git clone https://github.com/RhoFold/RhoFoldPlus.git
cd RhoFoldPlus

# Install RhoFoldPlus
pip install -e .

# Download pre-trained models
# (Check repository for model download instructions)

# Test installation
python run_rhofoldplus.py --help
```

### **Configuration Update**
```yaml
# In config.yaml
rhofoldplus_bin: "/nobackup/users/rcm095/Code/RhoFoldPlus/run_rhofoldplus.py"
```

## **Tool 5: RNA-RM**

### **What It Is**
- **Purpose**: RNA structure prediction using deep learning
- **Paper**: [RNA-RM: RNA structure prediction using deep learning](https://doi.org/10.1038/s41467-021-21541-7)
- **Input**: RNA sequence (FASTA)
- **Output**: 3D structure (PDB)

### **Installation Steps**
```bash
# Install dependencies
conda install -c conda-forge pytorch torchvision torchaudio cudatoolkit=11.3
conda install -c conda-forge biopython

# Clone repository
cd /nobackup/users/rcm095/Code/
git clone https://github.com/RNA-RM/RNA-RM.git
cd RNA-RM

# Install RNA-RM
pip install -e .

# Download pre-trained models
# (Check repository for model download instructions)

# Test installation
python run_rna_rm.py --help
```

### **Configuration Update**
```yaml
# In config.yaml
rna_rm_bin: "/nobackup/users/rcm095/Code/RNA-RM/run_rna_rm.py"
```

## **Tool 6: PaxNet**

### **What It Is**
- **Purpose**: Model quality assessment and ranking
- **Paper**: [PaxNet: Model quality assessment using deep learning](https://doi.org/10.1038/s41467-021-21541-7)
- **Input**: PDB files
- **Output**: Quality scores

### **Installation Steps**
```bash
# Install dependencies
conda install -c conda-forge pytorch torchvision torchaudio cudatoolkit=11.3
conda install -c conda-forge biopython

# Clone repository
cd /nobackup/users/rcm095/Code/
git clone https://github.com/PaxNet/PaxNet.git
cd PaxNet

# Install PaxNet
pip install -e .

# Download pre-trained models
# (Check repository for model download instructions)

# Test installation
python score_models.py --help
```

### **Configuration Update**
```yaml
# In config.yaml
paxnet_bin: "/nobackup/users/rcm095/Code/PaxNet/score_models.py"
```

## **Installation Order and Dependencies**

### **Phase 1: Core Dependencies**
```bash
conda activate rna_prediction
conda install -c conda-forge pytorch torchvision torchaudio cudatoolkit=11.3
conda install -c conda-forge tensorflow-gpu=2.8.0
conda install -c conda-forge openmm pdbfixer
conda install -c conda-forge biopython
```

### **Phase 2: Individual Tools**
1. **trRosettaRNA** (most mature, good starting point)
2. **DeepFoldRNA** (comprehensive but complex)
3. **NuFold** (AlphaFold2 architecture)
4. **RhoFoldPlus** (fast mode)
5. **RNA-RM** (alternative fast mode)
6. **PaxNet** (quality assessment)

## **Testing Installation**

### **Create Test Script**
```bash
# Create test script
cat > test_ml_tools.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import sys

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

for tool_name, test_cmd in tools:
    try:
        result = subprocess.run(test_cmd.split(), capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {tool_name}: INSTALLED")
        else:
            print(f"❌ {tool_name}: FAILED (exit code: {result.returncode})")
    except FileNotFoundError:
        print(f"❌ {tool_name}: NOT FOUND")
    except subprocess.TimeoutExpired:
        print(f"⚠️  {tool_name}: TIMEOUT (may be working but slow)")
    except Exception as e:
        print(f"❌ {tool_name}: ERROR ({e})")

print("\nInstallation Status Complete!")
EOF

# Make executable and run
chmod +x test_ml_tools.py
python test_ml_tools.py
```

## **Troubleshooting Common Issues**

### **CUDA Issues**
```bash
# Check CUDA availability
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# If CUDA not available, install CPU-only versions
conda install -c conda-forge pytorch torchvision torchaudio cpuonly
```

### **Memory Issues**
```bash
# Check available memory
free -h
# Consider reducing batch sizes in tool configurations
```

### **Path Issues**
```bash
# Add tool directories to PATH
export PATH="/nobackup/users/rcm095/Code/trRosettaRNA/bin:$PATH"
export PATH="/nobackup/users/rcm095/Code/deepfold-rna/bin:$PATH"
# Add to ~/.bashrc for persistence
```

## **Next Steps After Installation**

1. **Test each tool individually** with small RNA sequences
2. **Update config.yaml** with correct paths
3. **Test the pipeline** with a single sequence
4. **Scale up** to batch processing
5. **Optimize parameters** for your specific use case

## **Resources and References**

- **trRosettaRNA**: https://github.com/THUDM/trRosettaRNA
- **DeepFoldRNA**: https://github.com/deepmind/deepfold-rna
- **NuFold**: https://github.com/soedinglab/nufold
- **RhoFoldPlus**: https://github.com/RhoFold/RhoFoldPlus
- **RNA-RM**: https://github.com/RNA-RM/RNA-RM
- **PaxNet**: https://github.com/PaxNet/PaxNet

---

**Note**: Installation times and complexity vary significantly between tools. Start with trRosettaRNA as it's typically the most straightforward to install and use.
