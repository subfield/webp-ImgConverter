import os
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image

fileExtions = [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]

class ImageHandler(FileSystemEventHandler):
    def __init__(self, target_folder, index_file):
        self.target_folder = target_folder
        self.index_file = index_file

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext in fileExtions:
                self.convert_to_webp(file_path)

    def convert_to_webp(self, file_path):
        try:
            with Image.open(file_path) as img:
                webp_path = os.path.splitext(file_path)[0] + ".webp"
                if not os.path.exists(webp_path):
                    img.save(webp_path, format="WEBP")
                    print(f"Converted: {file_path} -> {webp_path}")
                    self.update_index_file(file_path, webp_path)
                else:
                    print(f"WebP already exists for: {file_path}")
        except Exception as e:
            print(f"Error converting {file_path}: {e}")

    def update_index_file(self, original_path, webp_path):
        if os.path.exists(self.index_file):
            with open(self.index_file, "r") as file:
                content = file.readlines()

            original_filename = os.path.basename(original_path)
            webp_filename = os.path.basename(webp_path)
            variable_name = os.path.splitext(webp_filename)[0]

            found_import = False
            found_export = False
            updated_lines = []
            export_start_index = None

            for i, line in enumerate(content):
                if original_filename in line or webp_filename in line:
                    found_import = True
                    updated_lines.append(line.replace(original_filename, webp_filename))
                else:
                    updated_lines.append(line)

                if "export const Img =" in line:
                    export_start_index = i

                if export_start_index is not None and f"{variable_name}," in line:
                    found_export = True

            if not found_import:
                import_line = f'import {variable_name} from "./{webp_filename}";\n'
                updated_lines.insert(0, import_line)
                print(f"Added new import for {webp_filename} in {self.index_file}")

            if export_start_index is not None and not found_export:
                for j in range(export_start_index + 1, len(updated_lines)):
                    if "}" in updated_lines[j]:
                        updated_lines[j] = f"    {variable_name},\n" + updated_lines[j]
                        print(f"Added {variable_name} to export block in {self.index_file}")
                        break

            with open(self.index_file, "w") as file:
                file.writelines(updated_lines)

            print(f"Updated {self.index_file} with {webp_filename}.")
        else:
            print(f"Index file {self.index_file} not found!")


def convert_existing_images(folder_path, index_file):
    print("Checking for existing images without WebP equivalents...")
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in fileExtions:
                webp_path = os.path.splitext(file_path)[0] + ".webp"
                if not os.path.exists(webp_path):
                    ImageHandler(folder_path, index_file).convert_to_webp(file_path)

def watch_folder(folder_path, index_file):
    convert_existing_images(folder_path, index_file)
    event_handler = ImageHandler(folder_path, index_file)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()

    print(f"Watching folder: {folder_path}")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def check_and_install_packages():
    required_packages = ["watchdog", "pillow"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        choice = input("Do you want to install the missing packages? (yes/no): ").strip().lower()
        if choice in ["yes", "y"]:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        else:
            print("Exiting program. Please install the required packages and try again.")
            sys.exit(1)

if __name__ == "__main__":
    check_and_install_packages()

    folder_to_watch = input("Enter the folder path to watch: ").strip()
    index_file_path = os.path.join(folder_to_watch, "index.ts")

    if os.path.isdir(folder_to_watch) and os.path.exists(index_file_path):
        watch_folder(folder_to_watch, index_file_path)
    else:
        print("Invalid folder path or index.ts file not found.")
