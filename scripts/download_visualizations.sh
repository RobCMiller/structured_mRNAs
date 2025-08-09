#!/bin/bash
# Download beautiful mRNA structure visualizations from server

echo "=== Downloading Beautiful mRNA Structure Visualizations ==="

# Set up directories
LOCAL_DIR="visualizations"
mkdir -p $LOCAL_DIR

# Download all visualization files
echo "Downloading visualization files from satori..."
rsync -avz satori:/orcd/data/mbathe/001/rcm095/RNA_predictions/output/comparisons/visualizations/ $LOCAL_DIR/

echo "✓ Visualizations downloaded to $LOCAL_DIR/"
echo ""
echo "Generated files:"
ls -la $LOCAL_DIR/*.pdf
ls -la $LOCAL_DIR/*.png
echo ""
echo "Beautiful visualizations ready for viewing! 🎨"
echo "Open the PDF files for high-quality vector graphics"
echo "Open the PNG files for quick preview"
