"""
HTML report generator for the file comparison tool.
Generates HTML reports from comparison results.
"""
import os
import csv
import datetime
from typing import List, Dict, Any, Optional, Tuple

from compare_utils import DiffResult, DataCatalog, ColumnInfo

def escapeHtml(text: str) -> str:
    """
    Escape HTML special characters in text.
    
    Args:
        text: Input text to escape
        
    Returns:
        HTML-escaped text
    """
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def formatDiffLine(line: str) -> str:
    """
    Format a diff line with appropriate HTML styling.
    
    Args:
        line: A line from the diff output
        
    Returns:
        HTML-formatted line with appropriate CSS class
    """
    escaped_line = escapeHtml(line)
    
    if line.startswith('+'):
        return f'<div class="diff-line added">{escaped_line}</div>'
    elif line.startswith('-'):
        return f'<div class="diff-line removed">{escaped_line}</div>'
    elif line.startswith('@@'):
        return f'<div class="diff-line info">{escaped_line}</div>'
    elif line.startswith('---') or line.startswith('+++'):
        return f'<div class="diff-line header">{escaped_line}</div>'
    else:
        return f'<div class="diff-line unchanged">{escaped_line}</div>'

def generateDataCatalogHtml(catalog: DataCatalog) -> str:
    """
    Generate HTML for displaying a data catalog.
    
    Args:
        catalog: DataCatalog object to render
        
    Returns:
        HTML string representation of the data catalog
    """
    if catalog is None:
        return ""
    
    summary = catalog.summarize()
    
    html = f"""
    <div class="catalog-section">
        <h3>File Metadata</h3>
        <div class="metadata-table">
            <table>
                <tr>
                    <th>Property</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>File Path</td>
                    <td>{escapeHtml(summary['file_path'])}</td>
                </tr>
                <tr>
                    <td>File Size</td>
                    <td>{summary['file_size_bytes']} bytes</td>
                </tr>
                <tr>
                    <td>Row Count</td>
                    <td>{summary['row_count']}</td>
                </tr>
                <tr>
                    <td>Column Count</td>
                    <td>{summary['column_count']}</td>
                </tr>
                <tr>
                    <td>Delimiter</td>
                    <td>{escapeHtml(summary['delimiter'])}</td>
                </tr>
            </table>
        </div>
        
        <h3>Column Analysis</h3>
        <div class="columns-accordion" onclick="toggleColumns(this)">Show Columns ▼</div>
        <div class="columns-container hidden">
    """
    
    # Add column details
    for header in catalog.headers:
        column = catalog.columns.get(header)
        if column:
            html += f"""
            <div class="column-card">
                <div class="column-header accordion" onclick="toggleColumn(this)">
                    <span class="column-name">{escapeHtml(column.name)}</span>
                    <span class="column-type">{column.data_type}</span>
                </div>
                <div class="column-details hidden">
                    <table>
                        <tr>
                            <th>Property</th>
                            <th>Value</th>
                        </tr>
                        <tr>
                            <td>Data Type</td>
                            <td>{column.data_type}</td>
                        </tr>
                        <tr>
                            <td>Null Count</td>
                            <td>{column.null_count} ({column.null_percentage}%)</td>
                        </tr>
                        <tr>
                            <td>Unique Values</td>
                            <td>{column.unique_count}</td>
                        </tr>
            """
            
            # Add min/max for numeric columns
            if column.data_type in ['integer', 'float']:
                html += f"""
                        <tr>
                            <td>Min Value</td>
                            <td>{column.min_value if column.min_value is not None else 'N/A'}</td>
                        </tr>
                        <tr>
                            <td>Max Value</td>
                            <td>{column.max_value if column.max_value is not None else 'N/A'}</td>
                        </tr>
                """
            
            # Add top values section
            html += """
                        <tr>
                            <td>Top Values</td>
                            <td>
                                <ul class="top-values">
            """
            
            for value, count in column.top_values:
                html += f"""
                                    <li>{escapeHtml(str(value))}: {count}</li>
                """
            
            html += """
                                </ul>
                            </td>
                        </tr>
                    </table>
                </div>
            </div>
            """
    
    html += """
        </div>
    </div>
    """
    
    return html

def generateCsvTableComparison(source_path: str, target_path: str, source_content: List[str], target_content: List[str], diff_lines: List[str]) -> str:
    """
    Generate a table-based comparison view for CSV files with cell-level difference highlighting.
    
    Args:
        source_path: Path to source file
        target_path: Path to target file
        source_content: Content of source file as lines
        target_content: Content of target file as lines
        diff_lines: Lines from the unified diff output
        
    Returns:
        HTML string with table comparison view
    """
    # Parse CSV content
    source_rows = [line.split(',') for line in source_content if line.strip()]
    target_rows = [line.split(',') for line in target_content if line.strip()]
    
    # Get headers
    source_headers = source_rows[0] if source_rows else []
    target_headers = target_rows[0] if target_rows else []
    
    # Use source headers as default, or merge if they differ
    headers = source_headers
    if source_headers != target_headers:
        # If headers differ, create a union of both
        headers = []
        seen = set()
        for h in source_headers + target_headers:
            if h not in seen:
                seen.add(h)
                headers.append(h)
    
    # Start building HTML table
    html = """<div class="csv-comparison">
    <div class="view-toggle-container">
        <div class="view-toggle">
            <button class="active" onclick="toggleView(this, 'diff-view')">Text Diff</button>
            <button onclick="toggleView(this, 'table-view')">Table View</button>
        </div>
    </div>
    <div id="diff-view" class="view-content diff-container">"""
    
    # Add the diff content in the Text Diff view
    for line in diff_lines:
        html += formatDiffLine(line)
    
    html += """</div>
    <div id="table-view" class="view-content hidden">
        <table class="comparison-table">
            <thead>
                <tr>
                    <th class="row-header">#</th>"""
    
    # Add column headers
    for header in headers:
        html += f"""<th colspan="2">{escapeHtml(header)}</th>"""
    
    html += """</tr>
                <tr>
                    <th></th>"""
    
    # Add source/target subheaders
    for _ in headers:
        html += """<th class="source-column">Source</th><th class="target-column">Target</th>"""
    
    html += """</tr>
            </thead>
            <tbody>"""
    
    # Determine the maximum number of rows to display
    max_rows = max(len(source_rows), len(target_rows))
    
    # Add data rows
    for row_idx in range(1, max_rows):  # Start at 1 to skip header row
        html += f"""
                    <tr>
                        <td class="row-header">{row_idx}</td>"""
        
        for col_idx, header in enumerate(headers):
            source_value = ""
            target_value = ""
            
            # Get source value if available
            if row_idx < len(source_rows) and col_idx < len(source_rows[row_idx]):
                source_value = source_rows[row_idx][col_idx]
            
            # Get target value if available
            if row_idx < len(target_rows) and col_idx < len(target_rows[row_idx]):
                target_value = target_rows[row_idx][col_idx]
            
            # Determine if values are different
            is_different = source_value != target_value
            different_class = "different" if is_different else ""
            
            html += f"""
                        <td class="source-cell {different_class}">{escapeHtml(source_value)}</td>
                        <td class="target-cell {different_class}">{escapeHtml(target_value)}</td>"""
        
        html += """
                    </tr>"""
    
    html += """
                </tbody>
            </table>
        </div>
    </div>"""
    
    return html

def generateJsonData(results: List[DiffResult], output_path: str) -> str:
    """
    Generate a JSON file containing all comparison data.
    
    Args:
        results: List of comparison results
        output_path: Path to the HTML output file
        
    Returns:
        Path to the generated JSON file
    """
    # Create the base filename from the HTML output path
    base_path = os.path.splitext(output_path)[0]
    json_path = f"{base_path}_data.json"
    
    # Build the data structure
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "comparison_results": []
    }
    
    for result in results:
        # Determine the status based on the DiffResult attributes
        if result.is_identical:
            status = "identical"
        elif result.source_only:
            status = "new"
        elif result.target_only:
            status = "missing"
        else:
            status = "different"
            
        comparison_data = {
            "source_path": result.source_path,
            "target_path": result.target_path,
            "status": status,
            "diff_lines": result.diff_lines,
            "is_csv": False
        }
        
        # Add CSV-specific data if available
        if result.source_path.endswith('.csv') and result.target_path.endswith('.csv') and result.source_content and result.target_content:
            comparison_data["is_csv"] = True
            comparison_data["source_content"] = result.source_content
            comparison_data["target_content"] = result.target_content
            
            # Parse CSV content for structured data
            source_rows = [line.split(',') for line in result.source_content if line.strip()]
            target_rows = [line.split(',') for line in result.target_content if line.strip()]
            
            # Get headers
            source_headers = source_rows[0] if source_rows else []
            target_headers = target_rows[0] if target_rows else []
            
            # Use source headers as default, or merge if they differ
            headers = source_headers
            if source_headers != target_headers:
                # If headers differ, create a union of both
                headers = []
                seen = set()
                for h in source_headers + target_headers:
                    if h not in seen:
                        seen.add(h)
                        headers.append(h)
            
            comparison_data["headers"] = headers
            comparison_data["source_rows"] = source_rows
            comparison_data["target_rows"] = target_rows
            
            # Add data catalog information
            if result.source_catalog is not None:
                # Convert the catalog to a serializable format
                source_catalog_data = {
                    "file_path": result.source_catalog.file_path,
                    "row_count": result.source_catalog.row_count,
                    "column_count": result.source_catalog.column_count,
                    "headers": result.source_catalog.headers,
                    "column_info": []
                }
                
                # Convert column information
                for column_name, column_info in result.source_catalog.columns.items():
                    column_data = {
                        "name": column_name,
                        "data_type": column_info.data_type,
                        "null_count": column_info.null_count,
                        "null_percentage": column_info.null_percentage,
                        "unique_count": column_info.unique_count,
                        "min_value": column_info.min_value,
                        "max_value": column_info.max_value,
                        "top_values": [(str(k), v) for k, v in column_info.top_values]
                    }
                    source_catalog_data["column_info"].append(column_data)
                
                comparison_data["source_catalog"] = source_catalog_data
            
            if result.target_catalog is not None:
                # Convert the catalog to a serializable format
                target_catalog_data = {
                    "file_path": result.target_catalog.file_path,
                    "row_count": result.target_catalog.row_count,
                    "column_count": result.target_catalog.column_count,
                    "headers": result.target_catalog.headers,
                    "column_info": []
                }
                
                # Convert column information
                for column_name, column_info in result.target_catalog.columns.items():
                    column_data = {
                        "name": column_name,
                        "data_type": column_info.data_type,
                        "null_count": column_info.null_count,
                        "null_percentage": column_info.null_percentage,
                        "unique_count": column_info.unique_count,
                        "min_value": column_info.min_value,
                        "max_value": column_info.max_value,
                        "top_values": [(str(k), v) for k, v in column_info.top_values]
                    }
                    target_catalog_data["column_info"].append(column_data)
                
                comparison_data["target_catalog"] = target_catalog_data
        
        data["comparison_results"].append(comparison_data)
    
    # Write the JSON file
    with open(json_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(data, f, indent=2)
    
    return json_path

def generateHtmlReport(diff_results: List[DiffResult], output_path: str) -> None:
    """
    Generate an HTML report from comparison results.
    
    Args:
        diff_results: List of comparison results
        output_path: Path to the HTML report output file
    """
    # Generate JSON data structure (but don't write to file)
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "comparison_results": []
    }
    
    for result in diff_results:
        # Determine the status based on the DiffResult attributes
        if result.is_identical:
            status = "identical"
        elif result.source_only:
            status = "new"
        elif result.target_only:
            status = "missing"
        else:
            status = "different"
            
        comparison_data = {
            "source_path": result.source_path,
            "target_path": result.target_path,
            "status": status,
            "diff_lines": result.diff_lines,
            "is_csv": False
        }
        
        # Add CSV-specific data if available
        if result.source_path.endswith('.csv') and result.target_path.endswith('.csv') and result.source_content and result.target_content:
            comparison_data["is_csv"] = True
            comparison_data["source_content"] = result.source_content
            comparison_data["target_content"] = result.target_content
            
            # Parse CSV content for structured data
            source_rows = [line.split(',') for line in result.source_content if line.strip()]
            target_rows = [line.split(',') for line in result.target_content if line.strip()]
            
            # Get headers
            source_headers = source_rows[0] if source_rows else []
            target_headers = target_rows[0] if target_rows else []
            
            # Use source headers as default, or merge if they differ
            headers = source_headers
            if source_headers != target_headers:
                # If headers differ, create a union of both
                headers = []
                seen = set()
                for h in source_headers + target_headers:
                    if h not in seen:
                        seen.add(h)
                        headers.append(h)
            
            comparison_data["headers"] = headers
            comparison_data["source_rows"] = source_rows
            comparison_data["target_rows"] = target_rows
            
            # Add data catalog information
            if result.source_catalog is not None:
                # Convert the catalog to a serializable format
                source_catalog_data = {
                    "file_path": result.source_catalog.file_path,
                    "row_count": result.source_catalog.row_count,
                    "column_count": result.source_catalog.column_count,
                    "headers": result.source_catalog.headers,
                    "column_info": []
                }
                
                # Convert column information
                for column_name, column_info in result.source_catalog.columns.items():
                    column_data = {
                        "name": column_name,
                        "data_type": column_info.data_type,
                        "null_count": column_info.null_count,
                        "null_percentage": column_info.null_percentage,
                        "unique_count": column_info.unique_count,
                        "min_value": column_info.min_value,
                        "max_value": column_info.max_value,
                        "top_values": [(str(k), v) for k, v in column_info.top_values]
                    }
                    source_catalog_data["column_info"].append(column_data)
                
                comparison_data["source_catalog"] = source_catalog_data
            
            if result.target_catalog is not None:
                # Convert the catalog to a serializable format
                target_catalog_data = {
                    "file_path": result.target_catalog.file_path,
                    "row_count": result.target_catalog.row_count,
                    "column_count": result.target_catalog.column_count,
                    "headers": result.target_catalog.headers,
                    "column_info": []
                }
                
                # Convert column information
                for column_name, column_info in result.target_catalog.columns.items():
                    column_data = {
                        "name": column_name,
                        "data_type": column_info.data_type,
                        "null_count": column_info.null_count,
                        "null_percentage": column_info.null_percentage,
                        "unique_count": column_info.unique_count,
                        "min_value": column_info.min_value,
                        "max_value": column_info.max_value,
                        "top_values": [(str(k), v) for k, v in column_info.top_values]
                    }
                    target_catalog_data["column_info"].append(column_data)
                
                comparison_data["target_catalog"] = target_catalog_data
        
        data["comparison_results"].append(comparison_data)
    
    # Convert data to JSON string for embedding in HTML
    import json
    json_data = json.dumps(data, ensure_ascii=False)
    
    # Start building the HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Comparison Report</title>
    <style>
        :root {
            --primary-color: #3498db;
            --secondary-color: #2ecc71;
            --danger-color: #e74c3c;
            --warning-color: #f39c12;
            --light-color: #f5f5f5;
            --dark-color: #333;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        header {
            background-color: var(--primary-color);
            color: white;
            text-align: center;
            padding: 20px;
        }
        
        h1 {
            margin-bottom: 5px;
        }
        
        .summary {
            padding: 20px;
            background-color: #f9f9f9;
            border-bottom: 1px solid #eee;
        }
        
        .stats-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }
        
        .stat-card {
            flex: 1;
            min-width: calc(25% - 20px);
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .stat-card h3 {
            margin-bottom: 10px;
            color: var(--dark-color);
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .identical {
            color: var(--secondary-color);
        }
        
        .different {
            color: var(--danger-color);
        }
        
        .new {
            color: var(--primary-color);
        }
        
        .missing {
            color: var(--warning-color);
        }
        
        .comparison-section {
            padding: 20px;
        }
        
        h2 {
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        
        .file-card {
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }
        
        .file-header {
            padding: 15px;
            background-color: #f5f5f5;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        }
        
        .file-paths {
            flex: 1;
        }
        
        .file-status {
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }
        
        .status-identical {
            background-color: var(--secondary-color);
        }
        
        .status-different {
            background-color: var(--danger-color);
        }
        
        .status-new {
            background-color: var(--primary-color);
        }
        
        .status-missing {
            background-color: var(--warning-color);
        }
        
        .diff-content {
            background-color: #f8f8f8;
            padding: 0;
            overflow-x: auto;
        }
        
        .catalog-content {
            padding: 15px;
            background-color: white;
        }
        
        .hidden {
            display: none;
        }
        
        .accordion {
            position: relative;
        }
        
        .accordion span {
            position: absolute;
            right: 15px;
        }
        
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
            border: 1px solid #ddd;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .comparison-table th, .comparison-table td {
            border: 1px solid #ddd;
            padding: 6px 10px;
            text-align: left;
        }
        
        .comparison-table th {
            background-color: #f2f2f2;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        
        .comparison-table .row-header {
            background-color: #f8f8f8;
            font-weight: 600;
            width: 40px;
            text-align: center;
        }
        
        .comparison-table .source-column {
            background-color: rgba(232, 244, 248, 0.5);
        }
        
        .comparison-table .target-column {
            background-color: rgba(232, 248, 235, 0.5);
        }
        
        .comparison-table .source-cell, .comparison-table .target-cell {
            font-family: monospace;
            white-space: nowrap;
        }
        
        .comparison-table .source-cell.different, .comparison-table .target-cell.different {
            background-color: #ffe8e8;
            position: relative;
        }
        
        .comparison-table .source-cell.different:after {
            content: "≠";
            position: absolute;
            right: 3px;
            top: 50%;
            transform: translateY(-50%);
            color: #e74c3c;
            font-weight: bold;
        }
        
        .view-toggle-container {
            margin-bottom: 15px;
            display: flex;
            justify-content: flex-start;
            align-items: center;
            border-bottom: 1px solid #eaeaea;
            padding-bottom: 10px;
            flex-wrap: wrap;
            position: sticky;
            top: 0;
            background-color: white;
            z-index: 100;
            padding: 10px;
        }
        
        .view-toggle {
            margin: 0;
            background-color: #f5f5f5;
            padding: 4px;
            border-radius: 4px;
            display: inline-flex;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            flex-shrink: 0;
        }
        
        .view-toggle button {
            padding: 8px 16px;
            margin-right: 0;
            border: 1px solid #ddd;
            background-color: #ffffff;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 13px;
            white-space: nowrap;
        }
        
        .view-toggle button:first-child {
            border-top-left-radius: 3px;
            border-bottom-left-radius: 3px;
        }
        
        .view-toggle button:last-child {
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
            margin-right: 0;
            border-left: none;
        }
        
        .view-toggle button.active {
            background-color: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
            font-weight: 500;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
        }
        
        .view-toggle button:hover:not(.active) {
            background-color: #f0f0f0;
        }
        
        .view-content {
            display: block;
            margin-top: 0;
            border-radius: 4px;
            overflow: auto;
        }
        
        .view-content.hidden {
            display: none;
        }
        
        /* Add responsive design for different screen sizes */
        @media (max-width: 768px) {
            .view-toggle-container {
                justify-content: center;
                padding: 8px;
            }
            
            .stat-card {
                min-width: calc(50% - 20px);
            }
            
            .view-toggle button {
                padding: 6px 12px;
                font-size: 12px;
            }
        }
        
        @media (max-width: 480px) {
            .view-toggle-container {
                padding: 5px;
            }
            
            .stat-card {
                min-width: 100%;
            }
            
            .view-toggle {
                width: 100%;
                display: flex;
            }
            
            .view-toggle button {
                flex: 1;
                padding: 8px 10px;
                text-align: center;
            }
            
            .comparison-table th, .comparison-table td {
                padding: 4px 6px;
                font-size: 12px;
            }
        }
        
        .csv-comparison {
            padding: 0;
            background-color: white;
            border-radius: 4px;
            overflow: hidden;
            border: 1px solid #eaeaea;
        }
        
        .diff-container {
            padding: 15px;
            background-color: #f8f8f8;
            border-radius: 0 0 4px 4px;
            line-height: 1.5;
            max-height: 500px;
            overflow: auto;
        }
        
        .diff-line {
            padding: 2px 5px;
            margin-bottom: 1px;
            border-radius: 2px;
            font-family: 'Consolas', 'Monaco', monospace;
            white-space: pre;
        }
        
        .diff-line.added {
            background-color: #e6ffed;
            color: #22863a;
        }
        
        .diff-line.removed {
            background-color: #ffeef0;
            color: #cb2431;
        }
        
        .diff-line.info {
            background-color: #f1f8ff;
            color: #0366d6;
        }
        
        .diff-line.unchanged {
            color: #24292e;
        }
        
        .catalog-section {
            margin-top: 20px;
            padding: 15px;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        .catalog-section h3 {
            margin-bottom: 15px;
            color: var(--primary-color);
            font-size: 18px;
            padding-bottom: 8px;
            border-bottom: 1px solid #eee;
            font-weight: 600;
        }
        
        .column-card {
            margin-bottom: 12px;
            border: 1px solid #eee;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .column-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 15px;
            background-color: #f8f8f8;
            cursor: pointer;
            border-bottom: 1px solid #eee;
        }
        
        .column-name {
            font-weight: 600;
            font-size: 15px;
            color: #333;
        }
        
        .column-type {
            background-color: #e8f4fd;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 0.85em;
            color: #0366d6;
            font-weight: 500;
        }
        
        .column-details {
            padding: 12px;
            background-color: #ffffff;
            display: none;
        }
        
        .column-details.visible {
            display: block;
        }
        
        .column-details table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
        }
        
        .column-details th, .column-details td {
            padding: 8px;
            border: 1px solid #eee;
            text-align: left;
        }
        
        .column-details th {
            background-color: #f8f8f8;
            width: 30%;
            font-weight: 600;
        }
        
        .top-values {
            list-style-type: none;
            padding-left: 0;
            margin: 0;
        }
        
        .top-values li {
            padding: 3px 0;
            border-bottom: 1px dotted #eee;
        }
        
        .column-header:hover {
            background-color: #f0f0f0;
        }
        
        .column-header:after {
            content: "▼";
            margin-left: 10px;
            font-size: 10px;
            color: #999;
        }
        
        .column-header.active:after {
            content: "▲";
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>File Comparison Report</h1>
            <p>Generated on <span id="timestamp">Loading...</span></p>
        </header>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="stats-container">
                <div class="stat-card">
                    <h3>Identical Files</h3>
                    <div class="stat-value identical" id="identical-count">0</div>
                </div>
                <div class="stat-card">
                    <h3>Different Files</h3>
                    <div class="stat-value different" id="different-count">0</div>
                </div>
                <div class="stat-card">
                    <h3>New Files</h3>
                    <div class="stat-value new" id="new-count">0</div>
                </div>
                <div class="stat-card">
                    <h3>Missing Files</h3>
                    <div class="stat-value missing" id="missing-count">0</div>
                </div>
            </div>
        </div>
        
        <div id="comparison-sections-container">
            <!-- Content will be loaded dynamically -->
            <div class="loading-container" style="text-align: center; padding: 50px;">
                <p>Loading comparison data...</p>
            </div>
        </div>
    </div>
    
    <script>
        // Embed the comparison data directly in the JavaScript
        const comparisonData = JSON_DATA_PLACEHOLDER;
        
        // Format the date as a human-readable string
        function formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleString();
        }
        
        // Toggle the display of diff content
        function toggleDiff(element) {
            const content = element.nextElementSibling;
            const span = element.querySelector('span');
            
            if (content.style.display === 'none' || !content.style.display) {
                content.style.display = 'block';
                span.textContent = 'Hide ▲';
            } else {
                content.style.display = 'none';
                span.textContent = 'Show ▼';
            }
        }
        
        // Toggle the display of catalog content
        function toggleCatalog(element) {
            const content = element.nextElementSibling;
            const span = element.querySelector('span');
            
            if (content.classList.contains('hidden')) {
                content.classList.remove('hidden');
                span.textContent = 'Hide ▲';
            } else {
                content.classList.add('hidden');
                span.textContent = 'Show ▼';
            }
        }
        
        // Toggle column details view
        function toggleColumn(element) {
            const content = element.nextElementSibling;
            
            if (content.classList.contains('hidden')) {
                content.classList.remove('hidden');
                content.classList.add('visible');
                element.classList.add('active');
            } else {
                content.classList.add('hidden');
                content.classList.remove('visible');
                element.classList.remove('active');
            }
        }
        
        // Toggle between different views (diff or table)
        function toggleView(buttonElement, viewId) {
            // Get all view-content elements in the same container
            const container = buttonElement.closest('.csv-comparison');
            const viewContents = container.querySelectorAll('.view-content');
            const buttons = buttonElement.parentElement.querySelectorAll('button');
            
            // Hide all view contents
            viewContents.forEach(content => {
                content.classList.add('hidden');
            });
            
            // Remove active class from all buttons
            buttons.forEach(button => {
                button.classList.remove('active');
            });
            
            // Show selected view and make button active
            container.querySelector('#' + viewId).classList.remove('hidden');
            buttonElement.classList.add('active');
        }
        
        // Format a diff line with the appropriate class
        function formatDiffLine(line) {
            let className = 'unchanged';
            if (line.startsWith('+')) {
                className = 'added';
            } else if (line.startsWith('-')) {
                className = 'removed';
            } else if (line.startsWith('@')) {
                className = 'info';
            }
            
            const escapedLine = line
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
                
            return `<div class="diff-line ${className}">${escapedLine}</div>`;
        }
        
        // Generate the table comparison view
        function generateTableView(result) {
            if (!result.is_csv) return '';
            
            let html = '<table class="comparison-table"><thead><tr><th class="row-header">#</th>';
            
            // Add column headers
            for (const header of result.headers) {
                html += `<th colspan="2">${header}</th>`;
            }
            
            html += '</tr><tr><th></th>';
            
            // Add source/target subheaders
            for (let i = 0; i < result.headers.length; i++) {
                html += '<th class="source-column">Source</th><th class="target-column">Target</th>';
            }
            
            html += '</tr></thead><tbody>';
            
            // Determine the maximum number of rows to display
            const maxRows = Math.max(
                result.source_rows ? result.source_rows.length : 0, 
                result.target_rows ? result.target_rows.length : 0
            );
            
            // Add data rows
            for (let rowIdx = 1; rowIdx < maxRows; rowIdx++) {  // Start at 1 to skip header row
                html += `<tr><td class="row-header">${rowIdx}</td>`;
                
                for (let colIdx = 0; colIdx < result.headers.length; colIdx++) {
                    let sourceValue = "";
                    let targetValue = "";
                    
                    // Get source value if available
                    if (result.source_rows && rowIdx < result.source_rows.length && colIdx < result.source_rows[rowIdx].length) {
                        sourceValue = result.source_rows[rowIdx][colIdx];
                    }
                    
                    // Get target value if available
                    if (result.target_rows && rowIdx < result.target_rows.length && colIdx < result.target_rows[rowIdx].length) {
                        targetValue = result.target_rows[rowIdx][colIdx];
                    }
                    
                    // Determine if values are different
                    const isDifferent = sourceValue !== targetValue;
                    const differentClass = isDifferent ? "different" : "";
                    
                    html += `<td class="source-cell ${differentClass}">${sourceValue}</td>`;
                    html += `<td class="target-cell ${differentClass}">${targetValue}</td>`;
                }
                
                html += '</tr>';
            }
            
            html += '</tbody></table>';
            return html;
        }
        
        // Generate the diff view for a comparison result
        function generateDiffView(result) {
            let html = '';
            for (const line of result.diff_lines) {
                html += formatDiffLine(line);
            }
            return html;
        }
        
        // Generate the catalog view for a comparison result
        function generateCatalogView(result, catalogKey) {
            if (!result[catalogKey]) return '';
            
            const catalog = result[catalogKey];
            let html = '<div class="catalog-content">';
            
            // Add column details
            for (const column of catalog.column_info) {
                html += `
                    <div class="column-card">
                        <div class="column-header" onclick="toggleColumn(this)">
                            <span class="column-name">${column.name}</span>
                            <span class="column-type">${column.data_type}</span>
                        </div>
                        <div class="column-details hidden">
                            <table>
                                <tr>
                                    <th>Property</th>
                                    <th>Value</th>
                                </tr>
                                <tr>
                                    <td>Data Type</td>
                                    <td>${column.data_type}</td>
                                </tr>
                                <tr>
                                    <td>Null Count</td>
                                    <td>${column.null_count} (${column.null_percentage}%)</td>
                                </tr>
                                <tr>
                                    <td>Unique Values</td>
                                    <td>${column.unique_count}</td>
                                </tr>
                `;
                
                // Add min/max for numeric columns
                if (column.data_type === 'integer' || column.data_type === 'float') {
                    html += `
                                <tr>
                                    <td>Min Value</td>
                                    <td>${column.min_value || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <td>Max Value</td>
                                    <td>${column.max_value || 'N/A'}</td>
                                </tr>
                    `;
                }
                
                // Add top values section
                html += `
                                <tr>
                                    <td>Top Values</td>
                                    <td>
                                        <ul class="top-values">
                `;
                
                if (column.top_values && column.top_values.length > 0) {
                    for (const [value, count] of column.top_values) {
                        html += `<li>${value}: ${count}</li>`;
                    }
                } else {
                    html += `<li>No top values available</li>`;
                }
                
                html += `
                                        </ul>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            return html;
        }
        
        // Process the comparison data and update the UI
        function processData() {
            try {
                const data = comparisonData;
                
                // Update timestamp
                document.getElementById('timestamp').textContent = formatDate(data.timestamp);
                
                // Initialize counters
                let identicalCount = 0;
                let differentCount = 0;
                let newCount = 0;
                let missingCount = 0;
                
                // Process the comparison results
                const results = data.comparison_results;
                const sectionsContainer = document.getElementById('comparison-sections-container');
                sectionsContainer.innerHTML = ''; // Clear loading message
                
                // Group results by status
                const groupedResults = {
                    'identical': [],
                    'different': [],
                    'new': [],
                    'missing': []
                };
                
                // Count results by status and group them
                for (const result of results) {
                    switch (result.status) {
                        case 'identical':
                            identicalCount++;
                            groupedResults.identical.push(result);
                            break;
                        case 'different':
                            differentCount++;
                            groupedResults.different.push(result);
                            break;
                        case 'new':
                            newCount++;
                            groupedResults.new.push(result);
                            break;
                        case 'missing':
                            missingCount++;
                            groupedResults.missing.push(result);
                            break;
                    }
                }
                
                // Update summary counts
                document.getElementById('identical-count').textContent = identicalCount;
                document.getElementById('different-count').textContent = differentCount;
                document.getElementById('new-count').textContent = newCount;
                document.getElementById('missing-count').textContent = missingCount;
                
                // Create sections for each status type
                const statusTypes = [
                    { name: 'Different Files', key: 'different', class: 'different' },
                    { name: 'Identical Files', key: 'identical', class: 'identical' },
                    { name: 'New Files', key: 'new', class: 'new' },
                    { name: 'Missing Files', key: 'missing', class: 'missing' }
                ];
                
                for (const statusType of statusTypes) {
                    const results = groupedResults[statusType.key];
                    if (results.length === 0) continue;
                    
                    let sectionHtml = `
                        <div class="comparison-section">
                            <h2>${statusType.name}</h2>
                    `;
                    
                    for (const result of results) {
                        sectionHtml += `
                            <div class="file-card">
                                <div class="file-header accordion" onclick="toggleDiff(this)">
                                    <div class="file-paths">
                                        <div>Source: ${result.source_path}</div>
                                        <div>Target: ${result.target_path}</div>
                                    </div>
                                    <span class="file-status status-${statusType.key}">${statusType.key.charAt(0).toUpperCase() + statusType.key.slice(1)}</span>
                                </div>
                                <div class="diff-content">
                        `;
                        
                        if (result.is_csv) {
                            sectionHtml += `
                                <div class="csv-comparison">
                                    <div class="view-toggle-container">
                                        <div class="view-toggle">
                                            <button class="active" onclick="toggleView(this, 'diff-view')">Text Diff</button>
                                            <button onclick="toggleView(this, 'table-view')">Table View</button>
                                        </div>
                                    </div>
                                    <div id="diff-view" class="view-content diff-container">
                                        ${generateDiffView(result)}
                                    </div>
                                    <div id="table-view" class="view-content hidden">
                                        ${generateTableView(result)}
                                    </div>
                                </div>
                            `;
                        } else {
                            sectionHtml += `<div class="diff-container">${generateDiffView(result)}</div>`;
                        }
                        
                        // Add data catalog information
                        if (result.source_catalog) {
                            sectionHtml += `
                                <div class="catalog-section">
                                    <h3>Source Data Catalog</h3>
                                    ${generateCatalogView(result, 'source_catalog')}
                                </div>
                            `;
                        }
                        
                        if (result.target_catalog) {
                            sectionHtml += `
                                <div class="catalog-section">
                                    <h3>Target Data Catalog</h3>
                                    ${generateCatalogView(result, 'target_catalog')}
                                </div>
                            `;
                        }
                        
                        sectionHtml += `
                                </div>
                            </div>
                        `;
                    }
                    
                    sectionHtml += `</div>`;
                    sectionsContainer.innerHTML += sectionHtml;
                }
                
            } catch (error) {
                console.error('Error processing comparison data:', error);
                document.getElementById('comparison-sections-container').innerHTML = `
                    <div style="text-align: center; padding: 50px; color: red;">
                        <p>Error processing comparison data: ${error.message}</p>
                    </div>
                `;
            }
        }
        
        // Process the data when the page loads
        window.addEventListener('DOMContentLoaded', processData);
    </script>
</body>
</html>"""

    # Replace the JSON data placeholder with the actual data
    html = html.replace("JSON_DATA_PLACEHOLDER", json_data)

    # Write the HTML to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Comparison report generated: {output_path}")
    except IOError as e:
        print(f"Error writing HTML report to {output_path}: {str(e)}")
