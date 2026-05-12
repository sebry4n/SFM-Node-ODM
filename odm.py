import sys
from pathlib import Path

from pyodm import Node
from pyodm.exceptions import TaskFailedError


client = Node("localhost", 3000)


dataset_dir = Path(__file__).resolve().parent / "sfm_dataset"

if not dataset_dir.is_dir():
    raise FileNotFoundError(f"Dataset directory does not exist: {dataset_dir}")

valid_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
images = sorted(
    str(file) for file in dataset_dir.iterdir()
    if file.is_file() and file.suffix.lower() in valid_extensions
)

if not images:
    raise FileNotFoundError(f"No images found in {dataset_dir}. Please check the path.")

print(f"Found {len(images)} images. Sending task to node...")


def _upload_progress(progress):
    print(f"  Upload: {progress:.1f}%", end="\r", flush=True)


def _status_progress(info):
    progress = getattr(info, "progress", None)
    if progress is not None:
        print(f"  Processing: {progress:.1f}%", end="\r", flush=True)


def _download_progress(progress):
    print(f"  Download: {progress:.1f}%", end="\r", flush=True)


task = client.create_task(
    images,
    {
        'dsm': True,
        'orthophoto-resolution': 2.0,
        'dem-resolution': 2.0,
        'feature-quality': 'high',
        'pc-quality': 'high',
        'min-num-features': 12000,
        'mesh-size': 300000,
        'use-3dmesh': True,
        'auto-boundary': True,
    },
    progress_callback=_upload_progress,
)
print()

print(f"Task created (uuid={task.uuid}). Processing in progress...")

try:
    task.wait_for_completion(status_callback=_status_progress)
    print()
except TaskFailedError:
    print()
    info = task.info()
    print(f"Task failed. Status: {info.status.name}", file=sys.stderr)
    try:
        output = task.output()
        if output:
            print("--- last task output ---", file=sys.stderr)
            print("\n".join(output[-30:]), file=sys.stderr)
    except Exception:
        pass
    raise

output_dir = Path(__file__).resolve().parent / "output_assets"
output_dir.mkdir(exist_ok=True)

print(f"Downloading assets to {output_dir}...")
task.download_assets(str(output_dir), progress_callback=_download_progress)
print()

print("Processing complete!")
