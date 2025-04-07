#!/usr/bin/env python3
"""
File Comparison Tool - Main Entry Point
Compares two files or directories and generates an HTML report of the differences.
"""
import argparse
import os
import sys
from typing import List, Optional, Tuple

from file_utils import get_file_paths, read_file
from compare_utils import compareFiles, compareDirectories
from html_generator import generateHtmlReport

def parseArguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare files and generate HTML report of differences"
    )
    parser.add_argument(
        "source", 
        nargs='?',
        default="examples/source_files",
        help="Source file or directory path (default: examples/source_files)"
    )
    parser.add_argument(
        "target", 
        nargs='?',
        default="examples/target_files",
        help="Target file or directory path to compare against (default: examples/target_files)"
    )
    parser.add_argument(
        "-o", "--output", 
        default="comparison_report.html",
        help="Output HTML report filename (default: comparison_report.html)"
    )
    parser.add_argument(
        "-r", "--recursive", 
        action="store_true",
        help="Recursively compare directories"
    )
    parser.add_argument(
        "--ignore", 
        nargs="+", 
        default=[],
        help="Patterns to ignore (e.g., *.tmp *.log)"
    )
    parser.add_argument(
        "-p", "--precision", 
        type=int,
        default=3,
        help="Decimal precision for number comparison (default: 3)"
    )
    parser.add_argument(
        "-c", "--catalog", 
        action="store_true",
        default=True,
        help="Generate data catalog for CSV files (enabled by default)"
    )
    parser.add_argument(
        "--no-catalog", 
        action="store_false",
        dest="catalog",
        help="Disable data catalog generation for CSV files"
    )
    return parser.parse_args()

def main() -> int:
    """Main function to handle file comparison workflow."""
    args = parseArguments()
    
    try:
        if os.path.isfile(args.source) and os.path.isfile(args.target):
            # Compare individual files
            source_content = read_file(args.source)
            target_content = read_file(args.target)
            
            if source_content is None or target_content is None:
                print("Error reading one of the files. Aborting.")
                return 1
                
            diff_results = compareFiles(
                args.source, 
                args.target, 
                source_content, 
                target_content,
                decimal_precision=args.precision,
                generate_catalog=args.catalog
            )
            generateHtmlReport([diff_results], args.output)
            print(f"Comparison report generated: {args.output}")
            
        elif os.path.isdir(args.source) and os.path.isdir(args.target):
            # Compare directories
            diff_results = compareDirectories(
                args.source, 
                args.target, 
                recursive=args.recursive,
                ignore_patterns=args.ignore,
                decimal_precision=args.precision,
                generate_catalog=args.catalog
            )
            generateHtmlReport(diff_results, args.output)
            print(f"Comparison report generated: {args.output}")
            
        else:
            print("Error: Both paths must be either files or directories")
            return 1
            
        return 0
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
