# mRNA Structure Prediction Pipeline

A comprehensive, elegant, and functional pipeline for predicting, analyzing, and comparing mRNA structures using multiple methods and parameters. Features beautiful visualizations with flatter CMYK color schemes and publication-ready aesthetics.

## 🚀 Quick Start

```bash
# Run with Tetrahymena P4-P6 domain (our benchmark sequence)
python scripts/mrna_structure_pipeline.py TETRAHYMENA

# Run with custom sequence file
python scripts/mrna_structure_pipeline.py YEAST data/yeast_sequence.fasta

# Generate beautiful visualizations for Tetrahymena
python scripts/mrna_visualization_pipeline.py TETRAHYMENA output/comparisons/

# Download visualizations to local machine
./scripts/download_visualizations.sh
```

## ⚠️ Important: Remote-Only Execution

**This pipeline is designed to run ONLY on the remote server (`satori`). Never run it locally, even for testing.**

### **Why Remote-Only?**
- **RNAfold Dependencies**: Requires ViennaRNA package installation
- **Computational Resources**: Designed for high-performance computing environment
- **Data Storage**: Configured for remote storage paths
- **Environment**: Uses conda environment on remote server

### **Remote Server Details**
- **Server**: `satori.mit.edu`
- **Python Version**: Python 3.6.8 (use `python3` command)
- **Default Python**: Python 2.7.5 (avoid using `python` command)
- **Working Directory**: `/orcd/data/mbathe/001/rcm095/RNA_predictions`
- **Conda Environment**: `rna_prediction`

### **Remote Execution Workflow**
1. **SSH to server**: `ssh satori`
2. **Navigate to project**: `cd /orcd/data/mbathe/001/rcm095/RNA_predictions`
3. **Activate environment**: `source /nobackup/users/jhdavis/cd_software/miniconda3/etc/profile.d/conda.sh && conda activate rna_prediction`
4. **Run pipeline**: `python3 scripts/mrna_structure_pipeline.py TETRAHYMENA`
5. **Generate visualizations**: `python3 scripts/mrna_visualization_pipeline.py TETRAHYMENA output/comparisons/`
6. **Run 3D predictions**: `python3 scripts/mrna_3d_structure_pipeline.py TETRAHYMENA --methods rosetta`
7. **Download results**: `./scripts/download_visualizations.sh` (from local machine)

### **Important: Code Changes Must Be Pushed to Remote Server**
- **All code changes must be pushed to the remote server**: The remote server is the final codebase where all processing and finalized code must live
- **Remote server is the source of truth**: All updates (including .md files) must be present on the remote server
- **Testing and execution**: All tests and predictions must be run on the remote server
- **Clean up old data**: Directories with old data or processing files should be cleaned up and removed from remote server
- **Push workflow**: After making local changes, always push to remote server before testing
- **Use rsync for file transfers**: Always use `rsync` over `scp` for transferring files to/from remote server

### **File Transfer Commands**
```bash
# Push changes to remote server (use rsync, not scp)
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' . satori:/orcd/data/mbathe/001/rcm095/RNA_predictions/

# Download results from remote server
rsync -avz satori:/orcd/data/mbathe/001/rcm095/RNA_predictions/output/ ./output/

# Sync specific files
rsync -avz README.md satori:/orcd/data/mbathe/001/rcm095/RNA_predictions/
rsync -avz scripts/ satori:/orcd/data/mbathe/001/rcm095/RNA_predictions/scripts/
```

### **3D Structure Prediction Pipeline Status**
- ✅ **Pipeline Working**: 3D structure prediction pipeline is fully functional
- ✅ **ROSETTA Integration**: ROSETTA predictions working with placeholder mode when not configured
- ✅ **SLURM Integration**: Jobs submitted and monitored successfully
- ✅ **Error Handling**: Comprehensive error handling and logging implemented
- ✅ **Testing Framework**: Test script validates pipeline setup and execution
- ✅ **File Naming**: Handles multiple naming conventions for comprehensive results
- ✅ **Placeholder Mode**: Creates test outputs when 3D structure tools aren't available

### **3D Structure Pipeline Usage**
```bash
# Test the pipeline setup
python3 scripts/test_3d_pipeline.py TETRAHYMENA --check-only

# Run 3D structure predictions with ROSETTA
python3 scripts/mrna_3d_structure_pipeline.py TETRAHYMENA --methods rosetta

# Run with multiple methods
python3 scripts/mrna_3d_structure_pipeline.py TETRAHYMENA --methods rosetta simrna farna

# Check results
ls -la output/3d_structures/TETRAHYMENA_5UTR/rosetta/output/default/
cat output/3d_structures/TETRAHYMENA_5UTR/TETRAHYMENA_5UTR_3d_results.json
```

### **Testing**
- **Tests use Tetrahymena P4-P6 domain**: Our benchmark sequence (135 nt)
- **Tests should ONLY be run on the remote server**: `python3 test_pipeline.py`
- **3D structure testing**: `python3 scripts/test_3d_pipeline.py TETRAHYMENA --check-only`
- **Local testing will skip remote-dependent tests** and show warnings
- **For full testing**: SSH to satori and run tests there

### **Important Commands**
```bash
# Always use python3, not python
python3 scripts/mrna_structure_pipeline.py TETRAHYMENA
python3 scripts/mrna_3d_structure_pipeline.py TETRAHYMENA --methods rosetta
python3 scripts/test_3d_pipeline.py TETRAHYMENA --check-only

# Check Python version
python3 --version  # Should show Python 3.6.8
python --version   # Shows Python 2.7.5 (avoid)

# Check available tools
which python3
which RNAfold
which sbatch
```

## 📁 Organized Output Structure

```
output/
├── sequences/
│   └── {SEQUENCE_PREFIX}_5UTR/
│       ├── rnafold/
│       │   ├── default/
│       │   │   ├── raw_output/          # Original RNAfold files
│       │   │   ├── parsed_results/      # Parsed JSON results
│       │   │   └── summary/            # Individual summaries
│       │   ├── temperature_25C/
│       │   ├── temperature_50C/
│       │   ├── maxspan_20/
│       │   ├── noGU/
│       │   └── partfunc/
│       ├── mfold/                      # Future: Mfold predictions
│       └── deep_learning/              # Future: Deep learning models
├── comparisons/
│   ├── {PREFIX}_comprehensive_results.json
│   ├── {PREFIX}_results_summary.csv
│   ├── {PREFIX}_results_summary.txt
│   └── visualizations/                 # 🎨 Beautiful plots
│       ├── {PREFIX}_energy_comparison.pdf
│       ├── {PREFIX}_structural_metrics.pdf
│       ├── {PREFIX}_structure_comparison.pdf
│       ├── {PREFIX}_temperature_sensitivity.pdf
│       ├── {PREFIX}_comprehensive_summary.pdf
│       └── how_to_interpret.md
```

## 🎯 Key Features

### **Clean & Elegant Design**
- **Single Script**: Everything in one well-organized file
- **Meaningful Names**: Clear, descriptive function and variable names
- **Organized Output**: Systematic directory structure for easy comparison
- **Multiple Formats**: JSON, CSV, and human-readable text summaries

### **Comprehensive Analysis**
- **Multiple Parameters**: Tests various RNAfold configurations
- **Automatic Comparison**: Identifies best energy structures
- **Rich Metrics**: Energy, base pairs, structural density analysis
- **Extensible**: Easy to add new prediction methods

### **Beautiful Visualizations** 🎨
- **Flatter CMYK Colors**: Professional color schemes with gun metal blues, teal greens, flat purples, and soft burnt oranges
- **Thick Axes**: 3.5pt axes with inverted tick marks
- **Clean Design**: No titles, minimal grid, publication-ready
- **Multiple Formats**: PDF (vector) and PNG (preview) outputs
- **High Resolution**: 300 DPI for print quality

### **User-Friendly**
- **Command Line Interface**: Simple, intuitive usage
- **Progress Feedback**: Clear status updates during execution
- **Error Handling**: Graceful failure handling
- **Documentation**: Comprehensive docstrings and help

## 🔧 Current Methods

### RNAfold Predictions
- **Default**: Standard RNAfold parameters
- **Temperature Variations**: 25°C, 37°C (default), 50°C
- **Parameter Variations**: Max base pair span, no GU pairs
- **Partition Function**: Base pair probability analysis

### 3D Structure Predictions
- **ROSETTA**: RNA structure prediction using ROSETTA framework
- **SimRNA**: Monte Carlo simulation for RNA 3D structure
- **FARNA**: Fragment assembly of RNA
- **RNAComposer**: Automated 3D structure modeling
- **Placeholder Mode**: Creates test outputs when tools aren't available

### **3D Structure Pipeline Features**
- **Automatic Tool Detection**: Checks for available 3D structure prediction tools
- **SLURM Integration**: Submits jobs to SLURM queue for parallel processing
- **Comprehensive Logging**: All operations logged to files for debugging
- **Error Handling**: Graceful failure handling with detailed error messages
- **Testing Framework**: `test_3d_pipeline.py` for validation and diagnostics

## 📊 Output Files

### **Individual Results**
- `structure.fold`: Raw RNAfold output
- `structure_ss.ps`: Secondary structure visualization
- `structure_dp.ps`: Dot plot visualization
- `*_parsed.json`: Parsed structure data

### **Comparison Files**
- `{PREFIX}_comprehensive_results.json`: Complete data in JSON format
- `{PREFIX}_results_summary.csv`: Spreadsheet-friendly comparison
- `{PREFIX}_results_summary.txt`: Human-readable summary with best results

### **Beautiful Visualizations** 🎨
- `{PREFIX}_energy_comparison.pdf/png`: Energy comparison across methods
- `{PREFIX}_structural_metrics.pdf/png`: Comprehensive structural analysis (base pairs, stability, density)
- `{PREFIX}_structure_comparison.pdf/png`: Visual structure comparison
- `{PREFIX}_temperature_sensitivity.pdf/png`: Parameter sensitivity analysis
- `{PREFIX}_comprehensive_summary.pdf/png`: All-in-one dashboard
- `how_to_interpret.md`: Comprehensive interpretation guide

### **3D Structure Results**
- `{PREFIX}_3d_results.json`: Complete 3D structure prediction results
- `{PREFIX}_3d_summary.txt`: Human-readable 3D structure summary
- `3d_structures/{PREFIX}_5UTR/{METHOD}/output/{PARAM}/`: 3D structure output files
- `3d_structures/{PREFIX}_5UTR/{METHOD}/logs/`: SLURM job logs and error files
- `*.pdb`: PDB format 3D structure files
- `*.trafl`: SimRNA trajectory files

## 🎨 Visualization Aesthetics

### **Color Scheme**
- **Gun Metal Blue (#2c3e50)**: Primary text, axes, labels
- **Flat Blue (#3498db)**: Standard structures, data points
- **Teal Green (#16a085)**: Base pair counts, structural complexity
- **Flat Purple (#8e44ad)**: Structural stability, energy analysis
- **Soft Burnt Orange (#d35400)**: Structural density, pairing efficiency
- **Flat Red (#e74c3c)**: Best energy structures, highlights

### **Design Elements**
- **Thick Axes**: 3.5pt with inverted tick marks (12pt length)
- **Clean Typography**: Arial/Helvetica fonts
- **No Titles**: Minimal, professional design
- **High Resolution**: 300 DPI for publication quality

## 🧬 Example Results

### **Tetrahymena P4-P6 Domain (135 nt) - Our Benchmark Sequence**
```
RNAFOLD_DEFAULT:
  Energy: -42.9 kcal/mol
  Base pairs: 41
  Structure: ((((...((((((....((((.((....(((.((..((((.((((((..((...((((....))))..))..))))))....)))).))))))).)))).))))))))))...((((....))))
  GC Content: 60.7%
  Base Pair Density: 0.328

RNAFOLD_TEMPERATURE_25C:
  Energy: -53.42 kcal/mol (BEST)
  Base pairs: 43
  Structure: ((.......))((((.((..(((....((((((.....(((.((..((((.((((((..((...((((....))))..))..)))))))....)))).)))))(((((....)))))))))))..)))..))))))
  GC Content: 60.7%
  Base Pair Density: 0.319

RNAFOLD_TEMPERATURE_50C:
  Energy: -32.3 kcal/mol
  Base pairs: 41
  Structure: ((((.((..(((....((((((.....(((.((..((((.((((((..((...((((....))))..))..))))))....)))).)))))(((((....)))))))))))..)))..))))))
  GC Content: 60.7%
  Base Pair Density: 0.331
```

## 🔮 Future Enhancements

### **Planned Features**
- **Mfold Integration**: Additional thermodynamic prediction method
- **Deep Learning Models**: EternaFold, RNA-FM integration
- **3D Structure Visualization**: PyMOL, ChimeraX integration
- **Statistical Analysis**: Confidence intervals, significance testing
- **Batch Processing**: Multiple sequence analysis
- **Web Interface**: User-friendly web application

### **Technical Improvements**
- **Performance Optimization**: Parallel processing for large datasets
- **Memory Management**: Efficient handling of large structures
- **Error Recovery**: Robust error handling and recovery
- **Testing Suite**: Comprehensive unit and integration tests

## 🛠️ Technical Details

### **Requirements**
- Python 3.6+
- RNAfold (ViennaRNA package)
- Standard Python libraries (json, csv, pathlib, etc.)
- Visualization libraries (matplotlib, numpy)

### **Architecture**
- **Object-Oriented**: Clean class-based design
- **Modular**: Separate prediction and visualization pipelines
- **Configurable**: Easy parameter modification
- **Extensible**: Simple to add new methods

## 📚 Usage Examples

```bash
# Analyze Tetrahymena P4-P6 domain (our benchmark sequence)
python scripts/mrna_structure_pipeline.py TETRAHYMENA

# Analyze custom sequence
python scripts/mrna_structure_pipeline.py YEAST data/yeast_5utr.fasta

# Generate beautiful visualizations for Tetrahymena
python scripts/mrna_visualization_pipeline.py TETRAHYMENA output/comparisons/

# Download visualizations to local machine
./scripts/download_visualizations.sh

# Use different working directory
python scripts/mrna_structure_pipeline.py TEST --work-dir /scratch/rna_analysis
```

## 🎯 Best Practices

### **Data Organization**
- **Consistent Naming**: Use descriptive prefixes for sequences
- **Backup Strategy**: Keep raw data and processed results separate
- **Version Control**: Track changes to analysis parameters
- **Documentation**: Document custom sequences and parameters

### **Quality Assurance**
- **Multiple Methods**: Always compare across different prediction approaches
- **Parameter Sensitivity**: Test different parameter combinations
- **Validation**: Compare with experimental data when available
- **Reproducibility**: Use consistent random seeds and parameters

### **Visualization Standards**
- **CMYK/Flat Colors**: Professional color schemes
- **Thick Axes**: 3.5pt with inverted tick marks
- **No Titles**: Clean, minimal design
- **High Resolution**: 300 DPI for publication quality
- **Vector Graphics**: PDF format for scalability

### **User Experience**
- **Simple Interface**: One command with optional parameters
- **Progress Feedback**: Clear status updates during execution
- **Error Messages**: Informative error handling
- **Documentation**: Comprehensive help and examples

## 🧹 Code Cleanup Summary

### **Completed Cleanup Tasks**
- ✅ **Removed redundant files**: Deleted outdated documentation and test scripts
- ✅ **Consolidated code**: Merged functionality into main pipeline scripts
- ✅ **Updated dependencies**: Streamlined requirements to only essential packages
- ✅ **Improved documentation**: Updated README with current features and usage
- ✅ **Cleaned up structure**: Removed unused imports and redundant methods
- ✅ **Standardized aesthetics**: Applied consistent flatter CMYK color scheme
- ✅ **Enhanced visualizations**: Removed GC content plots, added structural stability metrics
- ✅ **Updated tests**: Modernized test suite for current pipeline structure

### **Files Removed**
- `VISUALIZATION_GUIDE.md` - Information integrated into main README
- `STYLE_GUIDE.md` - Guidelines incorporated into main documentation
- `DEVELOPMENT_SUMMARY.md` - Outdated development notes
- `PROJECT_SUMMARY.md` - Information covered in main README
- `scripts/parse_results.py` - Functionality integrated into main pipeline
- `scripts/comprehensive_pipeline_test.sh` - Redundant test script
- `scripts/test_comprehensive_rnafold.sh` - Redundant test script
- `scripts/download_and_setup_sui3.sh` - Outdated setup script

### **Files Updated**
- `README.md` - Comprehensive documentation with current features
- `scripts/mrna_structure_pipeline.py` - Cleaned up and consolidated
- `scripts/mrna_visualization_pipeline.py` - Updated with new color scheme and features
- `requirements.txt` - Streamlined to essential dependencies
- `requirements_minimal.txt` - Updated minimal requirements
- `test_pipeline.py` - Modernized for current pipeline structure

### **Current Structure**
```
structure_prediction/
├── README.md                           # Comprehensive documentation
├── requirements.txt                    # Full dependencies
├── requirements_minimal.txt            # Minimal dependencies
├── test_pipeline.py                    # Updated test suite
├── scripts/
│   ├── mrna_structure_pipeline.py     # Main prediction pipeline
│   ├── mrna_visualization_pipeline.py # Beautiful visualizations
│   ├── download_visualizations.sh     # Download script
│   ├── run_predictions_slurm.sh      # SLURM job submission
│   ├── setup_remote_environment.sh    # Environment setup
│   ├── download_sui3_sequence.py      # Sequence download
│   └── investigate_remote.py          # Remote server investigation
├── data/                              # Input/output data
├── visualizations/                    # Generated plots
└── [other directories]                # Supporting files
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For questions and support, please open an issue on the project repository. 