#!/usr/bin/env python3
"""Script to investigate remote server capabilities and find SUI3 5'UTR sequence."""

import subprocess
import sys
from pathlib import Path


def run_remote_command(command: str) -> str:
    """Run a command on the remote server."""
    try:
        result = subprocess.run(
            ['ssh', 'satori', command],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e.stderr}")
        return ""


def check_remote_environment():
    """Check what's available on the remote server."""
    print("=== Investigating Remote Server Environment ===\n")
    
    # Check basic system info
    print("1. System Information:")
    system_info = run_remote_command("uname -a")
    print(system_info)
    
    # Check available modules
    print("\n2. Available Modules:")
    modules = run_remote_command("module avail 2>&1 | head -20")
    print(modules)
    
    # Check if RNAfold is available
    print("\n3. Checking for RNAfold:")
    rnafold_check = run_remote_command("which RNAfold")
    if rnafold_check.strip():
        print(f"RNAfold found at: {rnafold_check.strip()}")
        # Get RNAfold version
        version = run_remote_command("RNAfold --version 2>&1")
        print(f"Version: {version.strip()}")
    else:
        print("RNAfold not found in PATH")
    
    # Check for Python and conda
    print("\n4. Python Environment:")
    python_version = run_remote_command("python3 --version")
    print(f"Python version: {python_version.strip()}")
    
    conda_check = run_remote_command("conda --version")
    if conda_check.strip():
        print(f"Conda version: {conda_check.strip()}")
    else:
        print("Conda not found")
    
    # Check available GPUs
    print("\n5. GPU Information:")
    gpu_info = run_remote_command("nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits")
    if gpu_info.strip():
        print("Available GPUs:")
        print(gpu_info)
    else:
        print("No GPUs found or nvidia-smi not available")
    
    # Check storage space
    print("\n6. Storage Information:")
    storage_info = run_remote_command("df -h /orcd/data/mbathe/001/rcm095/RNA_predictions")
    print(storage_info)


def search_sui3_sequence():
    """Search for SUI3 5'UTR sequence."""
    print("\n=== Searching for SUI3 5'UTR Sequence ===\n")
    
    # Check if we can access common databases
    print("1. Checking for sequence databases:")
    
    # Try to find SUI3 in common locations
    possible_paths = [
        "/orcd/data/mbathe/001/rcm095/RNA_predictions",
        "/home/rcm095",
        "/nobackup/users/rcm095"
    ]
    
    for path in possible_paths:
        print(f"\nChecking {path}:")
        ls_result = run_remote_command(f"ls -la {path} 2>/dev/null | head -10")
        if ls_result.strip():
            print(ls_result)
        else:
            print("Path not accessible or empty")
    
    # Try to search for SUI3 in common databases
    print("\n2. Searching for SUI3 in common databases:")
    
    # Check if we can access NCBI or other databases
    ncbi_check = run_remote_command("which efetch 2>/dev/null || echo 'efetch not found'")
    if "not found" not in ncbi_check:
        print("NCBI tools available")
        # Try to fetch SUI3 sequence
        print("Attempting to fetch SUI3 sequence from NCBI...")
        sui3_fetch = run_remote_command("efetch -db nucleotide -id NM_001179998 -format fasta 2>/dev/null | head -5")
        if sui3_fetch.strip():
            print("SUI3 sequence found:")
            print(sui3_fetch)
        else:
            print("Could not fetch SUI3 sequence automatically")
    else:
        print("NCBI tools not available")


def main():
    """Main function."""
    print("Starting remote server investigation...\n")
    
    # Check if we can connect to the server
    print("Testing connection to satori...")
    test_connection = run_remote_command("echo 'Connection successful'")
    if "Connection successful" in test_connection:
        print("✓ Successfully connected to satori\n")
    else:
        print("✗ Failed to connect to satori")
        sys.exit(1)
    
    check_remote_environment()
    search_sui3_sequence()
    
    print("\n=== Investigation Complete ===")
    print("\nNext steps:")
    print("1. Install required tools on remote server if needed")
    print("2. Download SUI3 5'UTR sequence")
    print("3. Set up the prediction pipeline")


if __name__ == "__main__":
    main()
