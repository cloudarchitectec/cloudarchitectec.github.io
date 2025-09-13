import os
import re
import shutil
import argparse

def clean_filename(filename):
    # Keep the extension separate
    name, ext = os.path.splitext(filename)
    
    # Replace multiple hyphens with a single hyphen
    cleaned = re.sub('-+', '-', name)
    
    # Return the cleaned name with extension
    return cleaned + ext

def process_directory(input_dir, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.html'):
            old_path = os.path.join(input_dir, filename)
            new_filename = clean_filename(filename)
            new_path = os.path.join(output_dir, new_filename)
            
            if filename != new_filename:
                print(f'Copying with new name: {filename} -> {new_filename}')
            else:
                print(f'Copying: {filename}')
            shutil.copy2(old_path, new_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clean HTML filenames by removing excessive hyphens')
    parser.add_argument('input_dir', help='Input directory containing HTML files')
    parser.add_argument('output_dir', help='Output directory for processed files')
    
    args = parser.parse_args()
    
    print(f'Processing files from: {args.input_dir}')
    print(f'Saving to: {args.output_dir}')
    process_directory(args.input_dir, args.output_dir)
    print('Done!')
