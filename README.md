# File Comparison Tool

A Python-based automation tool for comparing files and directories and generating HTML reports of the differences with smart number handling.

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Features

- **File Comparison**: Compare individual files or entire directories
- **Smart Number Handling**: Configurable decimal precision for numeric value comparison (default: 3 decimal places)
- **CSV Data Catalog**: Automatically analyze CSV files and generate metadata including:
  - Column data types
  - Min/max values for numeric columns
  - Null and unique value statistics
  - Sample value distributions
- **Directory Support**: Recursively compare directory structures
- **Pattern Filtering**: Ignore specific file patterns
- **Interactive HTML Reports**: Generate detailed, responsive HTML reports with:
  - Visual diff highlighting
  - File status categorization (identical, different, source-only, target-only)
  - Data catalog visualizations for CSV files
  - Statistics summary
  - Collapsible sections for easy navigation
- **Pure Python**: No external dependencies required - uses only Python standard library

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/file-comparison-tool.git
   cd file-comparison-tool
   ```

2. No additional dependencies required - the tool uses only the Python standard library.

## 📊 Usage

### Command Line Interface

```bash
python main.py [SOURCE] [TARGET] [options]
```

#### Arguments:

- `SOURCE`: Path to the source file or directory (default: examples/source_files)
- `TARGET`: Path to the target file or directory to compare against (default: examples/target_files)

#### Options:

- `-o, --output FILE`: Specify output HTML report filename (default: comparison_report.html)
- `-r, --recursive`: Recursively compare directories
- `--ignore PATTERN [PATTERN ...]`: Patterns to ignore (e.g., *.tmp *.log)
- `-p, --precision N`: Decimal precision for number comparison (default: 3)
- `-c, --catalog`: Generate data catalog for CSV files (enabled by default)
- `--no-catalog`: Disable data catalog generation for CSV files

### Examples

Running without arguments uses the default directories:
```bash
python main.py
```

Compare two files:
```bash
python main.py examples/source_files/file1.csv examples/target_files/file1.csv
```

Compare two files with custom decimal precision:
```bash
python main.py examples/source_files/file1.csv examples/target_files/file1.csv -p 2
```

Compare two files without generating data catalog:
```bash
python main.py examples/source_files/file1.csv examples/target_files/file1.csv --no-catalog
```

Compare two directories recursively:
```bash
python main.py path/to/source path/to/target -r
```

Compare directories and ignore certain file types:
```bash
python main.py path/to/source path/to/target -r --ignore *.log *.tmp
```

Specify custom output file:
```bash
python main.py file1.txt file2.txt -o custom_report.html
```

## 📈 Example Output

When comparing the included example files with the default 3 decimal precision:
- `source_files/file1.csv`: `abc,1234.00100,qwert,2025/04/07`
- `target_files/file1.csv`: `abc,1234.00000,qwert,2025/04/07`

The HTML report will highlight the difference in the second column, where the values are treated as `1234.001` and `1234.000`.

![Example Report](https://via.placeholder.com/800x400?text=Example+Report+Screenshot)

## 🔎 Number Comparison Behavior

The tool intelligently handles number formatting:

- Numbers are compared with precision up to the specified decimal places (default: 3)
- Values that differ only beyond the specified precision are considered identical
- This applies to CSV files and any other text files with numeric values

For example, with default precision (3):
- `1234.00100` and `1234.00101` are considered identical (both rounded to `1234.001`)
- `1234.001` and `1234.002` are considered different

## 📊 Data Catalog Feature

For CSV files, the tool generates a comprehensive data catalog with the following information:

### File-level Metadata:
- File size
- Row count
- Column count
- Delimiter used

### Column-level Analysis:
- Inferred data type (integer, float, string, date, boolean)
- Null value count and percentage
- Unique value count
- Min/max values for numeric columns
- Most common values with their frequencies

The data catalog helps to understand the structure and content of CSV files being compared, making it easier to interpret differences and identify potential data quality issues.

## 🗂️ Project Structure

```
comparing_tool/
├── main.py             # Entry point and CLI interface
├── file_utils.py       # File handling utilities
├── compare_utils.py    # Comparison logic with smart number handling
├── html_generator.py   # HTML report generation
├── examples/           # Example files for testing
│   ├── source_files/   # Source directory with example files
│   │   ├── file1.csv
│   │   └── file2.csv
│   └── target_files/   # Target directory with example files
│       ├── file1.csv 
│       └── file2.csv
└── README.md           # Project documentation
```

## 💻 Technical Details

The tool follows these design principles:

- **Modularity**: Code is organized into logical modules
- **Type Hints**: Uses Python type hints for better code quality
- **Error Handling**: Robust error handling and reporting
- **No Dependencies**: Uses only the Python standard library for maximum compatibility

## 📝 Implementation Details

- The comparison is performed using Python's `difflib` library for text diff generation
- For numeric values, a preprocessing step normalizes numbers to a specified decimal precision
- CSV files are analyzed using a custom data catalog generator that infers data types and column statistics
- File handling is done with proper error handling and UTF-8 encoding support
- HTML reports use responsive design with modern CSS

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🔗 Related Projects

- [diff-match-patch](https://github.com/google/diff-match-patch) - Google's diff-match-patch library
- [difflib](https://docs.python.org/3/library/difflib.html) - Python's standard library diff tools
- [pandas-profiling](https://github.com/pandas-profiling/pandas-profiling) - Create HTML profiling reports from pandas DataFrames

---

Created with ❤️ using Python
