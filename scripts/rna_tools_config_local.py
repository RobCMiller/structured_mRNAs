"""
Local configuration file for rna_tools to override default settings.
This file should be placed in the same directory as rna_tools_config.py
or in a location where rna_tools can find it.
"""

# ROSETTA configuration
# Set the root directory for ROSETTA RNA modeling
# This should point to a directory where ROSETTA can store its working files
RNA_ROSETTA_RUN_ROOT_DIR_MODELING = "/tmp/rosetta_rna_modeling"

# Number of structures to generate (default: 10000)
RNA_ROSETTA_NSTRUC = 10

# Additional ROSETTA settings
# These can be customized based on your specific needs
ROSETTA_RNA_MODELING_CPUS = 30  # Use at least 30 CPUs per job
ROSETTA_RNA_MODELING_MAX_CPUS = 90  # Maximum total CPUs across all jobs
ROSETTA_RNA_MODELING_TIMEOUT = 3600  # 1 hour in seconds

# Note: This file should be imported or referenced by rna_tools
# You may need to set the PYTHONPATH to include this directory
# or copy it to the rna_tools installation directory
