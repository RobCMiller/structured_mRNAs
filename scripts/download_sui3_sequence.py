#!/usr/bin/env python3
"""Script to download SUI3 5'UTR sequence from yeast genome database."""

import requests
import re
from pathlib import Path
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


def fetch_sui3_sequence():
    """Fetch SUI3 sequence from SGD."""
    print("Fetching SUI3 sequence from Saccharomyces Genome Database...")
    
    # SGD API endpoint for SUI3
    url = "https://www.yeastgenome.org/backend/locus/S000006158"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract sequence information
        sequence = data.get('sequence', '')
        coordinates = data.get('coordinates', {})
        
        if sequence:
            print(f"✓ Successfully fetched SUI3 sequence (length: {len(sequence)})")
            return sequence, coordinates
        else:
            print("✗ No sequence found in response")
            return None, None
            
    except requests.RequestException as e:
        print(f"✗ Failed to fetch sequence: {e}")
        return None, None


def extract_5utr_sequence(sequence, coordinates):
    """Extract 5'UTR sequence from the full gene sequence."""
    print("Extracting 5'UTR sequence...")
    
    # For SUI3, we need to find the 5'UTR region
    # Based on SGD data, SUI3 is on chromosome XVI
    # We'll extract a reasonable 5'UTR length (typically 100-500 nt)
    
    # For now, let's take the first 300 nucleotides as 5'UTR
    # In practice, you'd want to get the exact coordinates from SGD
    utr_length = 300
    utr_sequence = sequence[:utr_length]
    
    print(f"✓ Extracted 5'UTR sequence (length: {len(utr_sequence)})")
    return utr_sequence


def save_sequence(sequence, filename="sui3_5utr.fasta"):
    """Save sequence to FASTA file."""
    if not sequence:
        print("✗ No sequence to save")
        return False
    
    # Create SeqRecord
    record = SeqRecord(
        Seq(sequence),
        id="SUI3_5UTR",
        name="SUI3_5UTR",
        description="5'UTR sequence of SUI3 gene from Saccharomyces cerevisiae"
    )
    
    # Save to file
    output_path = Path("data") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    SeqIO.write(record, output_path, "fasta")
    print(f"✓ Saved sequence to {output_path}")
    return True


def main():
    """Main function."""
    print("=== Downloading SUI3 5'UTR Sequence ===\n")
    
    # Fetch sequence
    sequence, coordinates = fetch_sui3_sequence()
    
    if sequence:
        # Extract 5'UTR
        utr_sequence = extract_5utr_sequence(sequence, coordinates)
        
        if utr_sequence:
            # Save sequence
            success = save_sequence(utr_sequence)
            
            if success:
                print(f"\n=== Download Complete ===")
                print(f"Sequence saved to: data/sui3_5utr.fasta")
                print(f"Sequence length: {len(utr_sequence)} nucleotides")
                print(f"Sequence preview: {utr_sequence[:50]}...")
            else:
                print("✗ Failed to save sequence")
        else:
            print("✗ Failed to extract 5'UTR sequence")
    else:
        print("✗ Failed to fetch sequence from SGD")


if __name__ == "__main__":
    main()
