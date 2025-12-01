import os

# Replace with your crates folder path
crate_folder = r'C:\Users\fulmi\Downloads\GF'

# List all .crate files
crate_files = [f for f in os.listdir(crate_folder) if f.endswith('.crate')]
print(f"Found {len(crate_files)} crates:")
for f in crate_files:
    print(f)
