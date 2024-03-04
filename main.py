import os
from src.upscale import upscale

for filename in os.listdir("./input"):
    filepath = os.path.join("./input/", filename)
    if filename.endswith(".mkv") or filename.endswith(".mp4"):
        print(f"Processing [{filename}]...")
        filename = filename.replace(".mkv", "") and filename.replace(".mp4", "")

        upscale(filepath, filename)
    else:
        continue
