"""
File comparison utilities for the comparison tool.
Provides functions to compare files and directories.
"""
import os
import re
import csv
import difflib
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Set, Union

from file_utils import read_file, get_file_paths, get_relative_path

class DiffResult:
    """Class to store the result of a file comparison."""
    
    def __init__(
        self, 
        source_path: str, 
        target_path: str, 
        is_identical: bool = True,
        diff_lines: List[str] = None,
        source_only: bool = False,
        target_only: bool = False,
        source_catalog: Optional['DataCatalog'] = None,
        target_catalog: Optional['DataCatalog'] = None,
        source_content: Optional[List[str]] = None,
        target_content: Optional[List[str]] = None
    ):
        self.source_path = source_path
        self.target_path = target_path
        self.is_identical = is_identical
        self.diff_lines = diff_lines or []
        self.source_only = source_only
        self.target_only = target_only
        self.source_catalog = source_catalog
        self.target_catalog = target_catalog
        self.source_content = source_content
        self.target_content = target_content
        
    def __str__(self) -> str:
        if self.source_only:
            return f"File exists only in source: {self.source_path}"
        elif self.target_only:
            return f"File exists only in target: {self.target_path}"
        elif self.is_identical:
            return f"Files are identical: {self.source_path} and {self.target_path}"
        else:
            return f"Files differ: {self.source_path} and {self.target_path}"

@dataclass
class ColumnInfo:
    """Class to store catalog information about a CSV column."""
    name: str
    data_type: str
    sample_values: List[Any] = field(default_factory=list)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    unique_values: Set[Any] = field(default_factory=set)
    null_count: int = 0
    row_count: int = 0
    
    @property
    def null_percentage(self) -> float:
        """Calculate percentage of null values."""
        if self.row_count == 0:
            return 0.0
        return round(100 * self.null_count / self.row_count, 2)
    
    @property
    def unique_count(self) -> int:
        """Return count of unique values."""
        return len(self.unique_values)
    
    @property
    def top_values(self) -> List[Tuple[Any, int]]:
        """Return most common values and their counts, up to 5."""
        if not hasattr(self, '_value_counts'):
            self._value_counts = Counter(self.sample_values)
        return self._value_counts.most_common(5)

@dataclass
class DataCatalog:
    """Class to store catalog information about a CSV file."""
    file_path: str
    row_count: int = 0
    column_count: int = 0
    headers: List[str] = field(default_factory=list)
    columns: Dict[str, ColumnInfo] = field(default_factory=dict)
    file_size_bytes: int = 0
    has_header: bool = True
    delimiter: str = ','
    encoding: str = 'utf-8'
    
    def get_column_info(self, column_name: str) -> Optional[ColumnInfo]:
        """Get information about a specific column."""
        return self.columns.get(column_name)
    
    def get_column_names(self) -> List[str]:
        """Get all column names."""
        return self.headers
    
    def summarize(self) -> Dict[str, Any]:
        """Get a summary of the data catalog."""
        return {
            'file_path': self.file_path,
            'file_size_bytes': self.file_size_bytes,
            'row_count': self.row_count,
            'column_count': self.column_count,
            'headers': self.headers,
            'has_header': self.has_header,
            'delimiter': self.delimiter,
            'encoding': self.encoding
        }

def normalizeNumber(value: str, decimal_precision: int = 3) -> str:
    """
    Normalize numeric values to a specified decimal precision.
    
    Args:
        value: String value to normalize if it's a number
        decimal_precision: Number of decimal places to preserve
        
    Returns:
        Normalized string value with limited decimal precision if it's a number,
        otherwise the original string
    """
    # Regular expression to match floating point numbers
    number_pattern = re.compile(r'^-?\d+\.\d+$')
    
    if number_pattern.match(value):
        try:
            # Convert to float, then format to specified precision
            float_value = float(value)
            return f"{float_value:.{decimal_precision}f}"
        except ValueError:
            return value
    return value

def normalizeCSVLine(line: str, decimal_precision: int = 3) -> str:
    """
    Normalize a CSV line by applying number formatting rules.
    
    Args:
        line: CSV line to normalize
        decimal_precision: Number of decimal places to preserve for numeric values
        
    Returns:
        Normalized CSV line with consistent number formatting
    """
    if not line:
        return line
        
    parts = line.split(',')
    normalized_parts = []
    
    for part in parts:
        normalized_parts.append(normalizeNumber(part.strip(), decimal_precision))
    
    return ','.join(normalized_parts)

def preprocessContent(content: List[str], decimal_precision: int = 3) -> List[str]:
    """
    Preprocess file content for comparison with normalized number formatting.
    
    Args:
        content: List of lines from the file
        decimal_precision: Number of decimal places to preserve for numeric values
        
    Returns:
        Preprocessed content with normalized number formatting
    """
    if not content:
        return content
    
    # Check if file appears to be CSV
    is_csv = ',' in content[0] if content else False
    
    if is_csv:
        return [normalizeCSVLine(line, decimal_precision) for line in content]
    else:
        # For non-CSV files, still normalize potential numeric values
        return [line for line in content]

def inferDataType(value: str) -> str:
    """
    Infer data type from a string value.
    
    Args:
        value: String value to analyze
        
    Returns:
        Inferred data type name
    """
    if value is None or value.strip() == '':
        return 'null'
    
    # Clean the value for analysis
    clean_value = value.strip()
    
    # Try to convert to integer
    try:
        int(clean_value)
        return 'integer'
    except ValueError:
        pass
    
    # Try to convert to float
    try:
        float(clean_value)
        return 'float'
    except ValueError:
        pass
    
    # Check for date formats
    date_patterns = [
        r'^\d{4}/\d{1,2}/\d{1,2}$',  # YYYY/MM/DD
        r'^\d{1,2}/\d{1,2}/\d{4}$',  # MM/DD/YYYY
        r'^\d{4}-\d{1,2}-\d{1,2}$',  # YYYY-MM-DD
    ]
    
    for pattern in date_patterns:
        if re.match(pattern, clean_value):
            return 'date'
    
    # Check for boolean-like values
    bool_values = ['true', 'false', 'yes', 'no', 'y', 'n', '1', '0', 't', 'f']
    if clean_value.lower() in bool_values:
        return 'boolean'
    
    # Default to string
    return 'string'

def createDataCatalog(file_path: str, content: Optional[List[str]] = None) -> DataCatalog:
    """
    Create a data catalog from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        content: Optional pre-loaded content
        
    Returns:
        DataCatalog object with metadata about the CSV file
    """
    if content is None:
        content = read_file(file_path)
        
    if not content or len(content) == 0:
        return DataCatalog(file_path=file_path)
    
    # Get file size
    try:
        file_size = os.path.getsize(file_path)
    except (OSError, IOError):
        file_size = 0
    
    # Auto-detect delimiter (simple version)
    potential_delimiters = [',', ';', '\t', '|']
    delimiter = ','
    for d in potential_delimiters:
        if d in content[0]:
            delimiter = d
            break
    
    # Initialize catalog
    catalog = DataCatalog(
        file_path=file_path,
        file_size_bytes=file_size,
        delimiter=delimiter
    )
    
    # Parse as CSV
    rows = []
    for line in content:
        if line.strip():  # Skip empty lines
            rows.append(line.split(delimiter))
    
    if not rows:
        return catalog
    
    # Assuming first row is header
    headers = [h.strip() for h in rows[0]]
    data_rows = rows[1:] if len(rows) > 1 else []
    
    catalog.headers = headers
    catalog.column_count = len(headers)
    catalog.row_count = len(data_rows)
    
    # Initialize column info
    for header in headers:
        catalog.columns[header] = ColumnInfo(name=header, data_type='unknown')
    
    # No data rows, infer types from headers and set placeholder values
    if not data_rows:
        # This handles the case of a single row CSV (headers only)
        # But our example doesn't have a header row, it's actually data
        # So let's add special handling for that case
        if len(rows) == 1:
            # Treat the "header" row as data if it's the only row in the file
            # First, make up generic column names
            generic_headers = [f"Column{i+1}" for i in range(len(headers))]
            
            # Store the original headers as the first data row
            data_row = headers
            
            # Reset catalog with generic headers
            catalog.headers = generic_headers
            catalog.columns = {}
            for header in generic_headers:
                catalog.columns[header] = ColumnInfo(name=header, data_type='unknown')
            catalog.row_count = 1
            
            # Analyze the single row as data
            for col_idx, header in enumerate(generic_headers):
                if col_idx < len(data_row):
                    value = data_row[col_idx].strip()
                    col_info = catalog.columns[header]
                    col_info.sample_values = [value]
                    col_info.row_count = 1
                    
                    if value:
                        col_info.unique_values.add(value)
                        col_info.data_type = inferDataType(value)
                        
                        # Handle numeric values
                        if col_info.data_type in ['integer', 'float']:
                            try:
                                num_val = float(value)
                                col_info.min_value = num_val
                                col_info.max_value = num_val
                            except ValueError:
                                pass
                    else:
                        col_info.null_count += 1
        return catalog
    
    # Analyze each column
    for col_idx, header in enumerate(headers):
        col_info = catalog.columns[header]
        col_info.row_count = len(data_rows)
        
        # Collect values for this column
        values = []
        for row in data_rows:
            if col_idx < len(row):
                value = row[col_idx].strip()
                values.append(value)
                
                # Track null/empty values
                if not value:
                    col_info.null_count += 1
                else:
                    col_info.unique_values.add(value)
                    
                    # Track min/max for numeric values
                    if col_info.data_type in ['integer', 'float']:
                        try:
                            num_val = float(value)
                            if col_info.min_value is None or num_val < col_info.min_value:
                                col_info.min_value = num_val
                            if col_info.max_value is None or num_val > col_info.max_value:
                                col_info.max_value = num_val
                        except ValueError:
                            pass
        
        # Store a sample of values (up to 100)
        col_info.sample_values = values[:min(100, len(values))]
        
        # Infer data type from non-empty values
        non_empty_values = [v for v in values if v]
        if non_empty_values:
            data_types = [inferDataType(v) for v in non_empty_values[:20]]  # Sample first 20 non-empty values
            most_common_type = Counter(data_types).most_common(1)[0][0]
            col_info.data_type = most_common_type
    
    return catalog

def compareFiles(
    source_path: str, 
    target_path: str, 
    source_content: Optional[List[str]] = None,
    target_content: Optional[List[str]] = None,
    decimal_precision: int = 3,
    generate_catalog: bool = True
) -> DiffResult:
    """
    Compare two files and return the differences.
    
    Args:
        source_path: Path to the source file
        target_path: Path to the target file
        source_content: Content of source file if already read
        target_content: Content of target file if already read
        decimal_precision: Number of decimal places to consider when comparing numbers
        generate_catalog: Whether to generate data catalogs for CSV files
        
    Returns:
        DiffResult object containing comparison results
    """
    # Read files if content not provided
    if source_content is None:
        source_content = read_file(source_path)
    if target_content is None:
        target_content = read_file(target_path)
        
    if source_content is None or target_content is None:
        # Handle error case where files couldn't be read
        return DiffResult(
            source_path, 
            target_path, 
            is_identical=False,
            diff_lines=["Error: Unable to read one or both files"],
            source_content=source_content,
            target_content=target_content
        )
    
    # Check if files are CSVs
    source_is_csv = source_path.lower().endswith('.csv') or (',' in source_content[0] if source_content else False)
    target_is_csv = target_path.lower().endswith('.csv') or (',' in target_content[0] if target_content else False)
    
    # Create data catalogs if needed
    source_catalog = None
    target_catalog = None
    if generate_catalog:
        if source_is_csv:
            source_catalog = createDataCatalog(source_path, source_content)
        if target_is_csv:
            target_catalog = createDataCatalog(target_path, target_content)
    
    # Preprocess content to normalize number formatting
    normalized_source = preprocessContent(source_content, decimal_precision)
    normalized_target = preprocessContent(target_content, decimal_precision)
    
    # Generate unified diff on normalized content
    diff = list(difflib.unified_diff(
        normalized_source,
        normalized_target,
        fromfile=source_path,
        tofile=target_path,
        lineterm=''
    ))
    
    is_identical = len(diff) == 0
    
    return DiffResult(
        source_path,
        target_path,
        is_identical=is_identical,
        diff_lines=diff,
        source_catalog=source_catalog,
        target_catalog=target_catalog,
        source_content=source_content,
        target_content=target_content
    )

def compareDirectories(
    source_dir: str, 
    target_dir: str, 
    recursive: bool = False, 
    ignore_patterns: List[str] = None,
    decimal_precision: int = 3,
    generate_catalog: bool = True
) -> List[DiffResult]:
    """
    Compare all files in two directories.
    
    Args:
        source_dir: Path to the source directory
        target_dir: Path to the target directory
        recursive: Whether to recursively compare subdirectories
        ignore_patterns: List of glob patterns to ignore
        decimal_precision: Number of decimal places to preserve for numeric comparisons
        generate_catalog: Whether to generate data catalogs for CSV files
        
    Returns:
        List of DiffResult objects
    """
    source_files = get_file_paths(source_dir, recursive, ignore_patterns)
    target_files = get_file_paths(target_dir, recursive, ignore_patterns)
    
    results = []
    
    # Convert to sets for faster lookups
    source_file_set = set(source_files)
    target_file_set = set(target_files)
    
    # Create dictionaries to store file names without paths for matching
    source_names = {}
    target_names = {}
    
    # Extract filenames and create lookup maps
    for path in source_files:
        filename = os.path.basename(path)
        source_names[filename] = path
    
    for path in target_files:
        filename = os.path.basename(path)
        target_names[filename] = path
    
    # Get the union of all file names
    all_filenames = set(source_names.keys()) | set(target_names.keys())
    
    # Process all files
    for filename in all_filenames:
        source_path = source_names.get(filename)
        target_path = target_names.get(filename)
        
        if source_path and target_path:
            # Both files exist, compare them
            source_content = read_file(source_path)
            target_content = read_file(target_path)
            
            # Get relative paths for display
            source_rel_path = get_relative_path(source_path, source_dir)
            target_rel_path = get_relative_path(target_path, target_dir)
            
            if source_content is None or target_content is None:
                # Error reading one of the files
                result = DiffResult(
                    source_rel_path,
                    target_rel_path,
                    is_identical=False,
                    diff_lines=["Error reading one of the files."],
                    source_content=source_content if source_content else [],
                    target_content=target_content if target_content else []
                )
            else:
                # Preprocess content to normalize number formatting
                normalized_source = preprocessContent(source_content, decimal_precision)
                normalized_target = preprocessContent(target_content, decimal_precision)
                
                # Generate unified diff on normalized content
                diff = list(difflib.unified_diff(
                    normalized_source,
                    normalized_target,
                    fromfile=source_rel_path,
                    tofile=target_rel_path,
                    lineterm=''
                ))
                is_identical = len(diff) == 0
                
                # Create data catalogs for CSV files if requested
                source_catalog = None
                target_catalog = None
                
                if generate_catalog and source_path.endswith('.csv') and target_path.endswith('.csv'):
                    source_catalog = createDataCatalog(source_path, source_content)
                    target_catalog = createDataCatalog(target_path, target_content)
                
                result = DiffResult(
                    source_rel_path,
                    target_rel_path,
                    is_identical=is_identical,
                    diff_lines=diff,
                    source_catalog=source_catalog,
                    target_catalog=target_catalog,
                    source_content=source_content,
                    target_content=target_content
                )
        elif source_path:
            # File exists only in source
            source_content = read_file(source_path)
            source_rel_path = get_relative_path(source_path, source_dir)
            
            # Create catalog for CSV files if requested
            source_catalog = None
            if generate_catalog and source_path.endswith('.csv') and source_content:
                source_catalog = createDataCatalog(source_path, source_content)
            
            result = DiffResult(
                source_rel_path,
                "",
                is_identical=False,
                source_only=True,
                diff_lines=[f"File exists only in source: {source_rel_path}"],
                source_catalog=source_catalog,
                source_content=source_content if source_content else []
            )
        else:
            # File exists only in target
            target_content = read_file(target_path)
            target_rel_path = get_relative_path(target_path, target_dir)
            
            # Create catalog for CSV files if requested
            target_catalog = None
            if generate_catalog and target_path.endswith('.csv') and target_content:
                target_catalog = createDataCatalog(target_path, target_content)
            
            result = DiffResult(
                "",
                target_rel_path,
                is_identical=False,
                target_only=True,
                diff_lines=[f"File exists only in target: {target_rel_path}"],
                target_catalog=target_catalog,
                target_content=target_content if target_content else []
            )
        
        results.append(result)
    
    return results

def get_relative_path(path: str, base_path: str) -> str:
    """Get the relative path from base_path to path."""
    try:
        return os.path.relpath(path, base_path)
    except ValueError:
        # Handle the case where paths are on different drives
        return path
