# Structured mRNAs Structure Prediction Pipeline

A comprehensive pipeline for predicting RNA secondary and tertiary structures, integrating RNAfold (ViennaRNA) for secondary structure prediction with ROSETTA for 3D structure generation.

## 🎯 **What This Pipeline Does**

This pipeline automates the complete workflow from RNA sequence to 3D structural models:

1. **Secondary Structure Prediction**: Uses RNAfold to predict 2D structure (dot-bracket notation)
2. **3D Structure Generation**: Uses ROSETTA to generate 7 structural models with different constraints
3. **Coupled Analysis**: Ensures secondary structure constraints improve 3D prediction accuracy
4. **Parallel Processing**: Runs all ROSETTA models simultaneously for efficiency

## 🚀 **Quick Start**

### **Prerequisites**
- SLURM workload manager
- Conda package manager
- Linux environment
- 8GB+ RAM per node

### **1. Clone & Setup**
```bash
git clone https://github.com/RobCMiller/structured_mRNAs.git
cd structured_mRNAs

# Create conda environment
conda create -n rna_prediction python=3.8
conda activate rna_prediction

# Install dependencies
conda install -c bioconda viennarna
conda install -c conda-forge numpy scipy matplotlib
```

### **2. Install ROSETTA**
```bash
# Download and build ROSETTA (requires license)
cd /path/to/build/directory
wget https://www.rosettacommons.org/downloads/rosetta_src_2025.31.post.dev+2.main.452533b21d.tgz
tar -xzf rosetta_src_2025.31.post.dev+2.main.452533b21d.tgz
cd rosetta_build
./scons.py -j8 mode=release bin
```

### **3. Run Pipeline**
```bash
# Submit to SLURM
sbatch scripts/rnafold_to_rosetta_pipeline.sh

# Monitor progress
squeue -u username
```

## 📁 **What You Get**

Each pipeline run creates a timestamped results directory:

```
results/20250812_14_30_00_RNAfold_Rosetta_results/
├── rnafold/           # Secondary structure predictions
├── rosetta/           # 3D structure predictions (7 models)
├── pdbs/              # Final PDB files (7 models)
└── pipeline_summary.txt
```

### **Output Models**
- **Model 1**: Sequence-only (no constraints)
- **Models 2-7**: With RNAfold secondary structure constraints (different seeds)

## 🔬 **How It Works**

### **Pipeline Flow**
```
RNA Sequence → RNAfold → Secondary Structure → ROSETTA → 7 3D Models
```

### **Key Features**
- **Coupled Analysis**: RNAfold and ROSETTA results are always paired
- **Constrained Modeling**: Secondary structure improves 3D prediction accuracy
- **Structural Diversity**: Different random seeds ensure varied conformations
- **Automated Workflow**: Single script handles entire pipeline

## 📊 **Example Results**

### **Input Sequence**
```
GGCAGGAAACCGGUGAGUAGCGCAGGGUUCGGUGUAGUCCGUGAGGCGAAAGCGCUAGCCGAAAGGCGAAACCGCUGAUGAGUAGCGCAGGGUUCGAUCCGGUAGCGAAAGCGCUAGCCGAAAGGCGAAACCGCU
```

### **RNAfold Secondary Structure**
```
..........((((...)))) (-42.90)
```

### **ROSETTA 3D Models**
- 7 PDB files with atomic coordinates
- Each ~356KB, ready for molecular visualization
- Compatible with PyMOL, Chimera, VMD

## 🛠 **Customization**

### **Different Sequences**
Modify the sequence in `scripts/rnafold_to_rosetta_pipeline.sh`:
```bash
SEQUENCE="your_rna_sequence_here"
```

### **Resource Allocation**
Adjust SLURM parameters in the script:
```bash
#SBATCH -c 12          # CPUs per ROSETTA job
#SBATCH --mem=8G       # Memory per job
#SBATCH -t 06:00:00    # Time limit
```

## 📚 **Documentation**

- **Complete Technical Details**: See `README_allthedetails.md`
- **Script Documentation**: Inline comments in all scripts
- **Example Outputs**: In `examples/` directory

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## 📄 **Citations**

If you use this pipeline in your research, please cite:

- **ROSETTA**: [Leaver-Fay et al. (2011)](https://doi.org/10.1007/978-1-61779-465-0_24)
- **ViennaRNA**: [Lorenz et al. (2011)](https://doi.org/10.1186/1748-7188-6-26)

## 📞 **Support**

- **Issues**: Use GitHub Issues
- **Documentation**: Check `README_allthedetails.md`
- **Logs**: Review SLURM output/error files

## 📈 **Performance**

- **RNAfold**: ~30 seconds
- **ROSETTA**: ~6 hours (7 parallel models)
- **Total Resources**: 84 CPUs, 56GB RAM
- **Output Size**: ~2.5MB per complete run

---

**Pipeline Version**: 1.0.0  
**Last Updated**: August 12, 2025  
**License**: MIT 