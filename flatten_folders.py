import os
import shutil
import sys

# The folder the script is run from (works with double-click, or by typing
# "cmd" in the File Explorer address bar and running: python flatten_folders.py)
parent = os.getcwd()
script_path = os.path.abspath(__file__)


def unique_path(dest_dir, filename):
    """Return a path in dest_dir that doesn't clash with an existing file."""
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(dest_dir, filename)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dest_dir, f"{base}_{counter}{ext}")
        counter += 1
    return candidate


def main():
    print(f"Parent folder: {parent}")
    print("This will MOVE every file in all subfolders into the parent folder.")
    if input("Continue? (y/n): ").strip().lower() != "y":
        print("Cancelled.")
        return

    moved = 0
    errors = 0

    for root, dirs, files in os.walk(parent):
        # Skip the parent folder itself - only process subfolders
        if os.path.abspath(root) == os.path.abspath(parent):
            continue

        for name in files:
            src = os.path.join(root, name)
            if os.path.abspath(src) == script_path:
                continue
            dst = unique_path(parent, name)
            try:
                shutil.move(src, dst)
                moved += 1
                print(f"Moved: {src}  ->  {dst}")
            except Exception as e:
                errors += 1
                print(f"ERROR moving {src}: {e}")

    print(f"\nDone. Files moved: {moved}, errors: {errors}")

    # Optionally delete the now-empty subfolders
    if input("Delete empty subfolders? (y/n): ").strip().lower() == "y":
        removed = 0
        # Walk bottom-up so nested empty folders are removed first
        for root, dirs, files in os.walk(parent, topdown=False):
            if os.path.abspath(root) == os.path.abspath(parent):
                continue
            try:
                if not os.listdir(root):
                    os.rmdir(root)
                    removed += 1
            except Exception as e:
                print(f"Could not remove {root}: {e}")
        print(f"Empty folders removed: {removed}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    input("\nPress Enter to exit...")
