# Structured mRNAs Structure Prediction Pipeline - Complete Technical Documentation

## **Overview**
This repository contains a comprehensive pipeline for predicting RNA secondary and tertiary structures, integrating RNAfold (ViennaRNA) for secondary structure prediction with ROSETTA for 3D structure generation. The pipeline is designed to run on SLURM-managed high-performance computing clusters.

## **Architecture & Logic**

### **Pipeline Flow**
1. **Input**: RNA sequence (FASTA format or direct sequence)
2. **RNAfold**: Generates secondary structure prediction (dot-bracket notation)
3. **ROSETTA**: Uses secondary structure as constraint for 3D structure prediction
4. **Output**: 7 structural models (1 unconstrained + 6 constrained by RNAfold)

### **Key Design Principles**
- **Coupled Analysis**: RNAfold and ROSETTA results are always paired
- **Constrained Modeling**: Secondary structure constraints improve 3D prediction accuracy
- **Parallel Processing**: 7 ROSETTA models run simultaneously for efficiency
- **Reproducible Seeds**: Different random seeds ensure structural diversity

## **Installation & Setup**

### **System Requirements**
- SLURM workload manager
- Conda package manager
- Linux environment (tested on CentOS/RHEL)
- Minimum 8GB RAM per node
- 12+ CPUs per ROSETTA job

### **1. Clone Repository**
```bash
git clone https://github.com/RobCMiller/structured_mRNAs.git
cd structured_mRNAs
```

### **2. Environment Setup**

#### **Create Conda Environment**
```bash
conda create -n rna_prediction python=3.8
conda activate rna_prediction
```

#### **Install Dependencies**
```bash
# Core dependencies
conda install -c bioconda viennarna  # RNAfold
conda install -c conda-forge numpy scipy matplotlib

# Additional tools
conda install -c bioconda blast muscle clustalo
```

### **3. ROSETTA Installation**

#### **Download ROSETTA**
```bash
# Navigate to build directory
cd /nobackup/users/username/Code/
wget https://www.rosettacommons.org/downloads/rosetta_src_2025.31.post.dev+2.main.452533b21d.tgz
tar -xzf rosetta_src_2025.31.post.dev+2.main.452533b21d.tgz
cd rosetta_build
```

#### **Build ROSETTA**
```bash
# Set environment variables
export ROSETTA3_DB=/path/to/rosetta_database
export ROSETTA3=/path/to/rosetta_build

# Configure and build
./scons.py -j8 mode=release bin
```

#### **Verify Installation**
```bash
# Test RNA denovo
./source/bin/rna_denovo.linuxgccrelease -help

# Test PDB extraction
./source/bin/extract_pdbs.linuxgccrelease -help
```

### **4. SLURM Configuration**

#### **Partition Setup**
```bash
# Check available partitions
sinfo -o '%P %D %T %C %m %e %a %l %L'

# Example partition configuration
#SBATCH -p sched_mit_mbathe
#SBATCH -c 12
#SBATCH --mem=8G
#SBATCH -t 06:00:00
```

#### **Resource Allocation**
- **RNAfold**: 1 CPU, 4GB RAM, 30 minutes
- **ROSETTA**: 12 CPUs per model, 8GB RAM, 6 hours
- **Total**: 84 CPUs, 56GB RAM for full pipeline

## **Pipeline Scripts**

### **1. Main Pipeline: `rnafold_to_rosetta_pipeline.sh`**

#### **Purpose**
Orchestrates the complete RNAfold → ROSETTA workflow

#### **Key Components**
```bash
# RNAfold execution
echo "SEQUENCE" | RNAfold > "$RESULTS_DIR/rnafold/rnafold_output.txt"

# Secondary structure extraction
SECSTRUCT=$(tail -1 "$RESULTS_DIR/rnafold/rnafold_output.txt" | sed 's/[[:space:]]*[^[:space:]]*$//')

# ROSETTA job submission
sbatch submit_rosetta_jobs.sh "$(pwd)" "$SECSTRUCT"
```

#### **Directory Structure Created**
```
results/<date>_<HR:MIN:SEC>_RNAfold_Rosetta_results/
├── rnafold/           # RNAfold secondary structure predictions
├── rosetta/           # ROSETTA 3D structure predictions (7 models)
├── pdbs/              # Final PDB files (7 models)
├── submit_rosetta_jobs.sh  # ROSETTA job submission script
└── pipeline_summary.txt    # Comprehensive summary report
```

### **2. ROSETTA Execution: `submit_rosetta_jobs.sh`**

#### **Generated Dynamically**
Created by main pipeline with specific secondary structure constraints

#### **7 Parallel Jobs**
1. **Model 1**: Sequence-only (no constraints)
2. **Model 2**: With RNAfold secondary structure
3. **Model 3**: With RNAfold secondary structure (seed 2)
4. **Model 4**: With RNAfold secondary structure (seed 3)
5. **Model 5**: With RNAfold secondary structure (seed 4)
6. **Model 6**: With RNAfold secondary structure (seed 5)
7. **Model 7**: With RNAfold secondary structure (seed 6)

#### **ROSETTA Commands**
```bash
rna_denovo.linuxgccrelease \
    -sequence "ggcaggaaaccggugaguagcgcaggguucgguguaguccgugaggcgaaagcgcuagccgaaaggcgaaaccgcugaugaguagcgcaggguucgauccgguagcgaaagcgcuagccgaaaggcgaaaccgcu" \
    -secstruct "$SECSTRUCT" \
    -nstruct 1 \
    -minimize_rna \
    -out:file:silent "model_X_with_secstruct.out"
```

### **3. PDB Extraction: `combine_and_extract_rosetta_models.sh`**

#### **Purpose**
Combines all silent files and extracts PDB structures

#### **Process**
1. **Combine Silent Files**: Merges 7 individual .out files
2. **Sequential Extraction**: Creates S_000001.pdb through S_000007.pdb
3. **Quality Check**: Verifies all models were extracted

## **Usage Examples**

### **Basic Pipeline Execution**
```bash
# Submit main pipeline
sbatch scripts/rnafold_to_rosetta_pipeline.sh

# Monitor progress
squeue -u username
sacct -j JOBID --format=JobID,JobName,State,ExitCode,Start,End,Elapsed
```

### **Custom Sequence Pipeline**
```bash
# Modify sequence in script
SEQUENCE="your_rna_sequence_here"
echo "$SEQUENCE" | RNAfold > "$RESULTS_DIR/rnafold/rnafold_output.txt"
```

### **Batch Processing**
```bash
# Create batch script for multiple sequences
for seq in sequences/*.fasta; do
    sbatch scripts/rnafold_to_rosetta_pipeline.sh "$seq"
done
```

## **Output Interpretation**

### **RNAfold Output**
```
GGCAGGAAACCGGUGAGUAGCGCAGGGUUCGGUGUAGUCCGUGAGGCGAAAGCGCUAGCCGAAAGGCGAAACCGCUGAUGAGUAGCGCAGGGUUCGAUCCGGUAGCGAAAGCGCUAGCCGAAAGGCGAAACCGCU
..........((((...)))) (-42.90)
```
- **Line 1**: Input sequence
- **Line 2**: Secondary structure + energy score

### **ROSETTA Silent Files**
- **Format**: Binary compressed format
- **Content**: Structural coordinates, scores, metadata
- **Size**: ~73-86KB per model
- **Extraction**: Use `extract_pdbs.linuxgccrelease`

### **PDB Files**
- **Format**: Standard Protein Data Bank format
- **Size**: ~356KB per model
- **Content**: 3D atomic coordinates
- **Visualization**: PyMOL, Chimera, VMD

## **Troubleshooting**

### **Common Issues**

#### **1. RNAfold Not Found**
```bash
# Solution: Activate conda environment
source /home/jhdavis/.start_cd_conda.sh
conda activate rna_prediction
which RNAfold
```

#### **2. ROSETTA GLIBCXX Error**
```bash
# Error: GLIBCXX_3.4.20 not found
# Solution: Run on compute node, not login node
sbatch scripts/rosetta_job.sh
```

#### **3. Secondary Structure Extraction Failure**
```bash
# Check RNAfold output
cat results/*/rnafold/rnafold_output.txt

# Verify structure format
tail -1 results/*/rnafold/rnafold_output.txt
```

#### **4. PDB Extraction Issues**
```bash
# Check silent file integrity
ls -la results/*/rosetta/*.out

# Verify extraction tool path
/nobackup/users/username/Code/rosetta_build/source/bin/extract_pdbs.linuxgccrelease -help
```

### **Debug Commands**
```bash
# Check job status
sacct -j JOBID --format=JobID,JobName,State,ExitCode,Start,End,Elapsed

# View SLURM logs
cat scripts/*.JOBID.output
cat scripts/*.JOBID.error

# Check file permissions
ls -la results/*/
```

## **Performance & Optimization**

### **Resource Usage**
- **RNAfold**: ~30 seconds, 1 CPU
- **ROSETTA**: ~6 hours, 84 CPUs total
- **PDB Extraction**: ~5 minutes, 1 CPU

### **Scaling Considerations**
- **Memory**: 8GB per node minimum
- **Storage**: ~2.5MB per complete pipeline run
- **Network**: Minimal I/O, mostly local computation

### **Optimization Tips**
1. **Parallel ROSETTA**: All 7 models run simultaneously
2. **Resource Allocation**: Match CPU count to available cores
3. **Storage**: Use local scratch directories for large outputs
4. **Monitoring**: Use SLURM job arrays for batch processing

## **File Organization**

### **Directory Structure**
```
structured_mRNAs/
├── config/                    # Configuration files
├── scripts/                   # SLURM and utility scripts
├── src/                       # Source code
├── docs/                      # Documentation
├── examples/                  # Example files
├── tests/                     # Test files
├── data/                      # Input data only
│   └── benchmark_data/        # Reference sequences
├── results/                   # All pipeline outputs
│   └── <date>_<time>_RNAfold_Rosetta_results/
│       ├── rnafold/           # Secondary structure predictions
│       ├── rosetta/           # 3D structure predictions
│       └── pdbs/              # Final PDB files
├── logs/                      # SLURM logs and pipeline logs
└── visualizations/            # Output plots and figures
```

### **Naming Convention**
- **Results**: `results/YYYYMMDD_HH_MM_SS_RNAfold_Rosetta_results/`
- **SLURM Logs**: `scripts/scriptname.JOBID.output/error`
- **ROSETTA Models**: `model_1_sequence_only.out`, `model_2_with_secstruct.out`
- **PDB Files**: `S_000001.pdb`, `S_000001_1.pdb`, etc.

## **Advanced Features**

### **Custom Constraints**
```bash
# Modify secondary structure constraints
SECSTRUCT="((((....))))"  # Custom structure
/nobackup/users/username/Code/rosetta_build/source/bin/rna_denovo.linuxgccrelease \
    -secstruct "$SECSTRUCT" \
    -sequence "$SEQUENCE"
```

### **Multiple Sequences**
```bash
# Process multiple sequences
for seq in sequences/*.fasta; do
    SEQUENCE=$(cat "$seq")
    # Run pipeline for each sequence
done
```

### **Integration with Other Tools**
```bash
# Use with visualization tools
pymol results/*/pdbs/*.pdb

# Analyze with RNA analysis tools
RNAfold --noPS < sequence.fasta
```

## **Maintenance & Updates**

### **Regular Tasks**
1. **Clean Old Results**: Remove results older than 30 days
2. **Update Dependencies**: Keep ROSETTA and ViennaRNA current
3. **Monitor Resources**: Track SLURM partition usage
4. **Backup Important Results**: Archive successful pipeline runs

### **Version Control**
```bash
# Update repository
git add .
git commit -m "Update pipeline with new features"
git push origin main

# Tag releases
git tag -a v1.0.0 -m "Stable pipeline release"
git push origin v1.0.0
```

## **Support & Contact**

### **Getting Help**
1. **Check Logs**: Review SLURM output and error files
2. **Verify Environment**: Ensure conda and ROSETTA are properly configured
3. **Resource Issues**: Check SLURM partition availability
4. **Documentation**: Refer to this README and inline code comments

### **Contributing**
1. **Fork Repository**: Create your own copy
2. **Test Changes**: Verify on test data before submitting
3. **Document Updates**: Update this README for new features
4. **Submit Pull Request**: Include detailed description of changes

---

**Last Updated**: August 12, 2025  
**Pipeline Version**: 1.0.0  
**ROSETTA Version**: 2025.31.post.dev+2.main.452533b21d  
**ViennaRNA Version**: 2.6.4
