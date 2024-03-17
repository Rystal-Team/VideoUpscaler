import torch, os, cv2, shutil
from tqdm import tqdm
from PIL import Image
from .RealESRGAN import RealESRGAN
from moviepy.editor import VideoFileClip, ImageSequenceClip, ImageClip


def extract_audio(video, filename):
    try:
        video_clip = VideoFileClip(video)
        audio = video_clip.audio

        print("Writing audio...")
        audio.write_audiofile(
            f"./temp/{filename}/audio.mp3", verbose=False, logger=None
        )
        print("Audio Written")
        video_clip.close()
        audio.close()
        return True
    except Exception as e:
        raise e


def extract_image(video, filename):
    cap = cv2.VideoCapture(video)

    frames_count, fps, width, height = (
        cap.get(cv2.CAP_PROP_FRAME_COUNT),
        cap.get(cv2.CAP_PROP_FPS),
        cap.get(cv2.CAP_PROP_FRAME_WIDTH),
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
    )

    progress = tqdm(total=frames_count, desc="Extracting Frames")
    if not os.path.exists(f"./temp/{filename}/"):
        os.mkdir(f"./temp/{filename}/")

    success, image = cap.read()
    count = 0
    while success:
        progress.update(1)
        cv2.imwrite(f"./temp/{filename}/{count}.png", image)
        success, image = cap.read()
        count += 1

    progress.close()

    return True, (frames_count, fps, width, height)


def upscale(video, filename, model):
    print(f"Processing {filename}!")

    ei_success, info = extract_image(video, filename)
    ea_success = extract_audio(video, filename)

    print(info[0], info[1], info[2], info[3])

    frames_count = len(
        [f for f in os.listdir(f"./temp/{filename}/") if f.endswith(".png")]
    )

    if not os.path.exists(f"./temp/{filename}/results"):
        os.mkdir(f"./temp/{filename}/results")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f'Device: {"cuda" if torch.cuda.is_available() else "cpu"}')

    model_scale = int(model.replace("x", ""))

    model = RealESRGAN(device, scale=model_scale)
    model.load_weights(f"weights/RealESRGAN_x{model_scale}.pth", download=True)

    progress = tqdm(total=frames_count, desc="Upscaling Frames")

    for frame in os.listdir(f"./temp/{filename}/"):
        if frame.endswith(".png"):
            image = Image.open(f"./temp/{filename}/{frame}").convert("RGB")
            scaled_image = model.predict(image)
            scaled_image.save(f"./temp/{filename}/results/{frame}")
            image.close()
            scaled_image.close()

            progress.update(1)

    progress.close()

    print(f"Concatenating Video...")

    clips = []
    fps = info[1]

    for clip in os.listdir(f"./temp/{filename}/results"):
        if clip.endswith(".png"):
            clip = os.path.join(f"./temp/{filename}/results", clip)
            clips.append(clip)

    clips.sort(key=lambda f: int("".join(filter(str.isdigit, f))))
    clip = ImageSequenceClip(clips, fps=fps)

    clip.write_videofile(
        f"./output/{filename}.mp4", fps=fps, audio=f"./temp/{filename}/audio.mp3"
    )
    clip.close()
    shutil.rmtree(f"./temp/{filename}/")

    print(f"Finished {filename}!")

    return
