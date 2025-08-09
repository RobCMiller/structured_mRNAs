# 3D Structure Prediction Troubleshooting Guide

This guide helps you identify and resolve common issues with the 3D structure prediction pipeline.

## 🎯 Recent Improvements (Latest Update)

### **Key Fixes Applied**
1. **Enhanced Error Handling**: Added comprehensive logging and error reporting
2. **Improved SLURM Integration**: Better job submission and monitoring
3. **Placeholder Mode**: Creates test outputs when tools aren't available
4. **Better Input Validation**: Validates sequence and structure formats
5. **Comprehensive Testing**: Added test script for validation

### **New Features**
- ✅ **Structured Logging**: All operations are logged to files and console
- ✅ **Automatic Directory Setup**: Creates all necessary directories
- ✅ **Tool Availability Detection**: Checks for required tools before running
- ✅ **Graceful Degradation**: Falls back to placeholder mode when tools unavailable
- ✅ **Comprehensive Testing**: `test_3d_pipeline.py` script for validation

### **Quick Start**
```bash
# 1. Test the pipeline setup
python scripts/test_3d_pipeline.py TETRAHYMENA --check-only

# 2. Run 3D structure predictions
python scripts/mrna_3d_structure_pipeline.py TETRAHYMENA --methods rosetta

# 3. Check results
ls -la output/3d_structures/TETRAHYMENA_5UTR/rosetta/output/
```

## 🚨 Common Issues and Solutions

### 1. **No RNAfold Results Found**

**Symptoms:**
```
❌ No RNAfold results found. Please run the structure prediction pipeline first.
```

**Solutions:**
1. **Run the structure prediction pipeline first:**
   ```bash
   python scripts/mrna_structure_pipeline.py TETRAHYMENA
   ```

2. **Check if comprehensive results exist:**
   ```bash
   ls -la /orcd/data/mbathe/001/rcm095/RNA_predictions/output/comparisons/
   ```

3. **Verify the sequence prefix:**
   - Make sure you're using the correct sequence prefix (e.g., `TETRAHYMENA`)
   - Check that the sequence name matches: `{PREFIX}_5UTR`

### 2. **SLURM Job Submission Failures**

**Symptoms:**
```
✗ Failed to submit SLURM job: Permission denied
✗ Failed to submit SLURM job: No such file or directory
```

**Solutions:**
1. **Check SLURM availability:**
   ```bash
   which sbatch
   squeue -u $USER
   ```

2. **Verify script permissions:**
   ```bash
   chmod +x scripts/mrna_3d_structure_pipeline.py
   ```

3. **Check SLURM partition access:**
   ```bash
   sinfo -p sched_cdrennan
   ```

4. **Verify resource limits:**
   ```bash
   scontrol show partition sched_cdrennan
   ```

### 3. **3D Structure Prediction Methods Not Available**

**Symptoms:**
```
⚠️  Method rosetta not available
⚠️  Method simrna not available
```

**Solutions:**
1. **Check if tools are installed:**
   ```bash
   # Check ROSETTA
   which rna_rosetta_run.py
   
   # Check SimRNA
   which SimRNA
   
   # Check FARNA
   which farna
   ```

2. **Install missing tools:**
   ```bash
   # For ROSETTA (requires specific installation)
   conda install -c conda-forge rosetta
   
   # For SimRNA (may require manual installation)
   # Follow SimRNA installation guide
   
   # For FARNA (may require manual installation)
   # Follow FARNA installation guide
   ```

3. **Use placeholder mode for testing:**
   - The pipeline now creates placeholder outputs when tools aren't available
   - This allows testing the pipeline structure without full tool installation

### 4. **Job Timeout Issues**

**Symptoms:**
```
✗ Job 12345 timed out after 86400 seconds
```

**Solutions:**
1. **Increase timeout in the code:**
   ```python
   # In wait_for_job_completion method
   timeout = 172800  # 48 hours instead of 24
   ```

2. **Check job status manually:**
   ```bash
   squeue -j 12345
   scontrol show job 12345
   ```

3. **Monitor resource usage:**
   ```bash
   sstat -j 12345
   ```

### 5. **Input File Format Issues**

**Symptoms:**
```
✗ ROSETTA error: Invalid input format
✗ SimRNA error: Sequence not found
```

**Solutions:**
1. **Check input file format:**
   ```bash
   # For ROSETTA
   cat output/3d_structures/TETRAHYMENA_5UTR/rosetta/input/default/input.fa
   
   # For SimRNA
   cat output/3d_structures/TETRAHYMENA_5UTR/simrna/input/default/input.txt
   ```

2. **Verify sequence and structure:**
   - Sequence should contain only A, C, G, U
   - Structure should be in dot-bracket notation
   - No extra characters or spaces

3. **Check file encoding:**
   ```bash
   file output/3d_structures/TETRAHYMENA_5UTR/rosetta/input/default/input.fa
   ```

### 6. **Output File Issues**

**Symptoms:**
```
No PDB files found in output directory
```

**Solutions:**
1. **Check output directory structure:**
   ```bash
   ls -la output/3d_structures/TETRAHYMENA_5UTR/rosetta/output/default/
   ```

2. **Check SLURM job logs:**
   ```bash
   cat output/3d_structures/TETRAHYMENA_5UTR/rosetta/output/default/logs/rosetta_default_*.out
   cat output/3d_structures/TETRAHYMENA_5UTR/rosetta/output/default/logs/rosetta_default_*.err
   ```

3. **Verify job completion:**
   ```bash
   sacct -j 12345 --format=JobID,JobName,State,ExitCode
   ```

### 7. **Memory and Resource Issues**

**Symptoms:**
```
✗ Job failed: Out of memory
✗ Job failed: CPU limit exceeded
```

**Solutions:**
1. **Adjust SLURM configuration:**
   ```python
   # In __init__ method
   self.slurm_config = {
       "partition": "sched_cdrennan",
       "time": "48:00:00",
       "mem": "256000",  # Increase memory
       "cpus_per_task": 8,  # Reduce CPU usage
       "gpus": 1,  # Reduce GPU usage
       "nodes": 1,
       "mpi_ranks": 4,  # Reduce MPI ranks
       "exclude": "node2021"
   }
   ```

2. **Check available resources:**
   ```bash
   sinfo -o "%P %A %D %T %N %G"
   ```

3. **Use smaller test sequences:**
   - Start with shorter sequences (50-100 nt)
   - Gradually increase sequence length

### 8. **Environment Issues**

**Symptoms:**
```
✗ Module not found: rna_rosetta_run
✗ Conda environment not activated
```

**Solutions:**
1. **Check conda environment:**
   ```bash
   conda info --envs
   conda activate rna_prediction
   ```

2. **Verify module availability:**
   ```bash
   module avail
   module load rosetta  # if available
   ```

3. **Check PATH:**
   ```bash
   echo $PATH
   which python
   which rna_rosetta_run.py
   ```

## 🔍 Diagnostic Commands

### **Check Pipeline Status**
```bash
# Check if 3D structure directories exist
ls -la output/3d_structures/

# Check if RNAfold results exist
ls -la output/comparisons/

# Check SLURM job status
squeue -u $USER

# Check recent job history
sacct -u $USER --starttime=2024-01-01
```

### **Verify Input Data**
```bash
# Check comprehensive results
cat output/comparisons/TETRAHYMENA_5UTR_comprehensive_results.json | jq 'keys'

# Check sequence and structure
cat output/comparisons/TETRAHYMENA_5UTR_comprehensive_results.json | jq '.results.rnafold_default.sequence'
cat output/comparisons/TETRAHYMENA_5UTR_comprehensive_results.json | jq '.results.rnafold_default.structure'
```

### **Monitor Job Progress**
```bash
# Check job logs in real-time
tail -f output/3d_structures/TETRAHYMENA_5UTR/rosetta/output/default/logs/rosetta_default_*.out

# Check error logs
tail -f output/3d_structures/TETRAHYMENA_5UTR/rosetta/output/default/logs/rosetta_default_*.err
```

## 🛠️ Testing and Validation

### **Test with Minimal Configuration**
```bash
# Test with just ROSETTA and a small sequence
python scripts/mrna_3d_structure_pipeline.py TEST --methods rosetta

# Check if placeholder files are created
ls -la output/3d_structures/TEST_5UTR/rosetta/output/default/
```

### **Validate Output Files**
```bash
# Check PDB file format
head -20 output/3d_structures/TETRAHYMENA_5UTR/rosetta/output/default/*.pdb

# Validate JSON results
python -c "import json; json.load(open('output/3d_structures/TETRAHYMENA_5UTR/TETRAHYMENA_5UTR_3d_results.json'))"
```

## 📞 Getting Help

### **Log Files to Check**
1. **Pipeline logs:**
   ```
   output/3d_structures/{SEQUENCE}_5UTR/logs/3d_pipeline.log
   ```

2. **SLURM job logs:**
   ```
   output/3d_structures/{SEQUENCE}_5UTR/{METHOD}/output/{PARAM}/logs/{METHOD}_{PARAM}_*.out
   output/3d_structures/{SEQUENCE}_5UTR/{METHOD}/output/{PARAM}/logs/{METHOD}_{PARAM}_*.err
   ```

3. **System logs:**
   ```bash
   dmesg | tail -50
   journalctl -u slurmctld --since "1 hour ago"
   ```

### **Common Error Codes**
- **Exit Code 0:** Success
- **Exit Code 1:** General error
- **Exit Code 137:** Out of memory (SIGKILL)
- **Exit Code 143:** Timeout (SIGTERM)

### **Support Resources**
1. **SLURM Documentation:** https://slurm.schedmd.com/
2. **ROSETTA Documentation:** https://www.rosettacommons.org/docs/
3. **SimRNA Documentation:** https://genesilico.pl/SimRNA/
4. **FARNA Documentation:** https://rosie.graylab.jhu.edu/farna/

## 🎯 Best Practices

### **Before Running 3D Predictions**
1. ✅ Run structure prediction pipeline first
2. ✅ Verify RNAfold results exist
3. ✅ Check available computational resources
4. ✅ Test with small sequences first
5. ✅ Monitor job submissions

### **During Execution**
1. ✅ Monitor job status regularly
2. ✅ Check log files for errors
3. ✅ Verify output file generation
4. ✅ Track resource usage
5. ✅ Keep backup of important results

### **After Completion**
1. ✅ Validate output files
2. ✅ Check result quality
3. ✅ Archive successful results
4. ✅ Document any issues encountered
5. ✅ Update troubleshooting guide

## 🚀 Next Steps

### **Immediate Actions**
1. **Test the pipeline setup:**
   ```bash
   python scripts/test_3d_pipeline.py TETRAHYMENA --check-only
   ```

2. **Run a small test:**
   ```bash
   python scripts/mrna_3d_structure_pipeline.py TETRAHYMENA --methods rosetta
   ```

3. **Monitor the results:**
   ```bash
   tail -f output/3d_structures/TETRAHYMENA_5UTR/logs/3d_pipeline.log
   ```

### **If Issues Persist**
1. **Check the troubleshooting guide above** for specific error symptoms
2. **Review log files** in the `logs` directory
3. **Verify SLURM job status** using `squeue` and `sacct`
4. **Test with smaller sequences** to isolate issues
5. **Contact system administrators** for SLURM or resource issues

### **Success Indicators**
- ✅ 3D structure directories created successfully
- ✅ SLURM jobs submitted and completed
- ✅ PDB files generated in output directories
- ✅ JSON results file created with comprehensive data
- ✅ Summary file generated with readable results

## 📞 Support and Resources

### **Documentation**
- **README.md**: Main project documentation
- **3d_structure_troubleshooting.md**: This troubleshooting guide
- **test_3d_pipeline.py**: Validation and testing script

### **Log Files**
- **Pipeline logs**: `output/3d_structures/{SEQUENCE}_5UTR/logs/3d_pipeline.log`
- **SLURM job logs**: `output/3d_structures/{SEQUENCE}_5UTR/{METHOD}/output/{PARAM}/logs/`
- **Error logs**: Check `.err` files in SLURM job logs

### **External Resources**
- **SLURM Documentation**: https://slurm.schedmd.com/
- **ROSETTA Documentation**: https://www.rosettacommons.org/docs/
- **SimRNA Documentation**: https://genesilico.pl/SimRNA/
- **FARNA Documentation**: https://rosie.graylab.jhu.edu/farna/

---

**Last Updated**: December 2024
**Version**: 1.0
**Status**: Ready for Production Use
