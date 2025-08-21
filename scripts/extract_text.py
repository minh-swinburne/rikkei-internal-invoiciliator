import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.services.pdf_processor import PDFProcessor

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_text.py <input_pdf_path> <output_txt_path>")
        sys.exit(1)

    input_pdf = Path(sys.argv[1])
    output_txt = Path(sys.argv[2])

    processor = PDFProcessor()
    text = processor.extract_text(input_pdf)

    if text:
        output_txt.write_text(text, encoding="utf-8")
        print(f"Extracted text saved to {output_txt}")
    else:
        print("Failed to extract text from PDF.")
