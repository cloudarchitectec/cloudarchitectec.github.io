# Blog Conversion Scripts

## HTML to Hugo Converter

This script converts HTML files (e.g., Medium exports) to Hugo-compatible markdown files with proper frontmatter and image bundling.

### Setup

1. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment**:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

```bash
python3 scripts/html2hugo.py <source_folder> <target_folder>
```

Example:
```bash
python3 scripts/html2hugo.py clean-titles/ cloudarchitectec/content/posts
```

### Features

- Creates folder structure using original HTML filename
- Downloads and bundles images locally
- Generates Hugo-compatible frontmatter with metadata
- Handles Unsplash images properly
- Adds layout suffixes for CSS styling
- Extracts tags, titles, and descriptions from HTML meta

### Deactivating Virtual Environment

When done, deactivate the virtual environment:
```bash
deactivate
```