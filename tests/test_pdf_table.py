"""
Test script for table extraction from PDF using PyMuPDF
Based on PyMuPDF table recognition and extraction capabilities
"""

import pymupdf
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def extract_tables_from_page(page: pymupdf.Page) -> list[dict]:
    """
    Extract tables from a PDF page using PyMuPDF's find_tables method
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        List of table data
    """
    tables_data = []
    
    try:
        # Find tables on the page
        tables = page.find_tables()
        
        print(f"Found {len(tables.tables)} tables on page {page.number + 1}")
        
        for table_index, table in enumerate(tables):
            print(f"\nTable {table_index + 1}:")
            print(f"  Bounding box: {table.bbox}")
            print(f"  Rows: {table.row_count}")
            print(f"  Columns: {table.col_count}")
            
            # Extract table data
            table_data = table.extract()
            
            # Clean and process the data
            processed_data = []
            for row_index, row in enumerate(table_data):
                cleaned_row = []
                for cell in row:
                    # Clean cell content
                    cleaned_cell = str(cell).strip() if cell else ""
                    cleaned_row.append(cleaned_cell)
                processed_data.append(cleaned_row)
            
            tables_data.append({
                'table_index': table_index,
                'bbox': table.bbox,
                'row_count': table.row_count,
                'col_count': table.col_count,
                'data': processed_data
            })
            
            # Display first few rows
            print(f"  First 5 rows:")
            for i, row in enumerate(processed_data[:5]):
                print(f"    Row {i}: {row}")
            
    except Exception as e:
        print(f"Error extracting tables from page {page.number + 1}: {e}")
    
    return tables_data

def save_tables_as_csv(tables: dict, output_dir: Path, filename_base: str) -> None:
    """
    Save extracted tables as CSV files
    
    Args:
        tables: List of table dictionaries
        output_dir: Output directory path
        filename_base: Base filename for output files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    for page_num, page_tables in tables.items():
        for table in page_tables:
            table_index = table['table_index']
            data = table['data']
            
            if data:
                # Create DataFrame
                df = pd.DataFrame(data)
                
                # Save as CSV
                csv_filename = f"{filename_base}_page{page_num + 1}_table{table_index + 1}.csv"
                csv_path = output_dir / csv_filename
                df.to_csv(csv_path, index=False, header=False)
                print(f"Saved table to: {csv_path}")

def analyze_pdf_tables(pdf_path: str | Path) -> dict:
    """
    Main function to analyze tables in a PDF file
    
    Args:
        pdf_path: Path to the PDF file
    """
    print(f"Analyzing PDF: {pdf_path}")
    print("=" * 60)
    
    try:
        # Open the PDF
        doc = pymupdf.open(pdf_path)
        print(f"PDF opened successfully. Pages: {len(doc)}")
        
        all_tables = {}
        total_tables = 0
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            print(f"\n--- Page {page_num + 1} ---")
            
            # Extract tables from this page
            page_tables = extract_tables_from_page(page)
            
            if page_tables:
                all_tables[page_num] = page_tables
                total_tables += len(page_tables)
        
        print(f"\n" + "=" * 60)
        print(f"SUMMARY:")
        print(f"Total pages processed: {len(doc)}")
        print(f"Total tables found: {total_tables}")
        print(f"Pages with tables: {len(all_tables)}")
        
        # Save tables as CSV files
        if all_tables:
            pdf_name = Path(pdf_path).stem
            output_dir = Path("data") / "output" / "tables"
            save_tables_as_csv(all_tables, output_dir, pdf_name)
            
            # Save summary as JSON
            summary = {
                'pdf_file': str(pdf_path),
                'total_pages': len(doc),
                'total_tables': total_tables,
                'pages_with_tables': len(all_tables),
                'tables_by_page': {}
            }
            
            for page_num, page_tables in all_tables.items():
                summary['tables_by_page'][page_num] = [
                    {
                        'table_index': table['table_index'],
                        'bbox': table['bbox'],
                        'row_count': table['row_count'],
                        'col_count': table['col_count']
                    }
                    for table in page_tables
                ]
            
            json_path = output_dir / f"{pdf_name}_summary.json"
            with open(json_path, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"Summary saved to: {json_path}")
        
        doc.close()
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return {}
    
    return all_tables

def test_table_extraction_with_settings() -> None:
    """
    Test table extraction with different settings
    """
    # Get the first PDF file from test directory
    test_dir = Path(__file__).parent.parent / "data" / "input" / "test"
    pdf_files = list(test_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in test directory")
        return
    
    for pdf_path in pdf_files:
        print(f"Using PDF file: {pdf_path}")
        
        # Test basic table extraction
        print("\n" + "=" * 80)
        print("BASIC TABLE EXTRACTION")
        print("=" * 80)
        basic_tables = analyze_pdf_tables(pdf_path)
        
        # Test with custom table detection settings
        print("\n" + "=" * 80)
        print("CUSTOM SETTINGS TABLE EXTRACTION")
        print("=" * 80)
        
        try:
            doc = pymupdf.open(pdf_path)
            
            for page_num in range(min(3, len(doc))):  # Test first 3 pages
                page = doc[page_num]
                print(f"\n--- Page {page_num + 1} with custom settings ---")
                
                # Try different table finding strategies
                strategies = [
                    {"strategy": "lines_strict"},
                    {"strategy": "lines"},
                    {"strategy": "explicit"},
                ]
                
                for i, strategy in enumerate(strategies):
                    try:
                        print(f"\nStrategy {i+1}: {strategy}")
                        tables = page.find_tables(**strategy)
                        print(f"Found {len(tables.tables)} tables with {strategy['strategy']} strategy")
                        
                        for j, table in enumerate(tables[:2]):  # Show first 2 tables
                            print(f"  Table {j+1}: {table.row_count}x{table.col_count}")
                            if table.row_count > 0:
                                data = table.extract()
                                print(f"    Sample row: {data[0] if data else 'No data'}")
                                
                    except Exception as e:
                        print(f"    Error with {strategy['strategy']}: {e}")
            
            doc.close()
            
        except Exception as e:
            print(f"Error in custom settings test: {e}")

if __name__ == "__main__":
    print("PyMuPDF Table Extraction Test")
    print(f"PyMuPDF version: {pymupdf.version[0]}")
    print("=" * 80)
    
    # Run the test
    test_table_extraction_with_settings()