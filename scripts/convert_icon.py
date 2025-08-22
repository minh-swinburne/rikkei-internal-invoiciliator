"""
Icon conversion script to create ICO files from PNG for PyInstaller.
"""
import sys
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def convert_png_to_ico(png_path: Path, ico_path: Path, sizes: list = None):
    """Convert PNG to ICO format with multiple sizes."""
    if not PIL_AVAILABLE:
        print("PIL (Pillow) not available. Please install with: pip install Pillow")
        return False
    
    if sizes is None:
        sizes = [16, 32, 48, 64, 128, 256]  # Common icon sizes
    
    try:
        # Open the PNG image
        img = Image.open(png_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create different sizes
        icon_sizes = []
        for size in sizes:
            resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
            icon_sizes.append(resized_img)
        
        # Save as ICO
        img.save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in icon_sizes]
        )
        
        print(f"Successfully converted {png_path} to {ico_path}")
        print(f"Created ICO with sizes: {sizes}")
        return True
        
    except Exception as e:
        print(f"Error converting PNG to ICO: {e}")
        return False


def main():
    """Main function to convert icons."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    assets_dir = project_root / "src" / "assets"
    
    # Input PNG file
    png_path = assets_dir / "icon.png"
    
    if not png_path.exists():
        print(f"Error: PNG icon not found at {png_path}")
        return 1
    
    # Output ICO file
    ico_path = assets_dir / "icon.ico"
    
    # Convert
    if convert_png_to_ico(png_path, ico_path):
        print(f"\nIcon conversion completed successfully!")
        print(f"ICO file created at: {ico_path}")
        print("\nYou can now use this ICO file with PyInstaller:")
        print(f"pyinstaller --icon={ico_path} --onefile your_script.py")
        return 0
    else:
        print("Icon conversion failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
