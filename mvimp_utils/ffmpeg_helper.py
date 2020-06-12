import cv2
import os
import PIL

def fps_info(src: str) -> float:
    """video fps lookup"""
    video = cv2.VideoCapture(src)
    # Find OpenCV version
    major_ver, _, _ = cv2.__version__.split(".")
    if int(major_ver) < 3:
        fps = video.get(cv2.cv.CV_CAP_PROP_FPS)
    else:
        fps = video.get(cv2.CAP_PROP_FPS)
    video.release()

    return "%.2f" % fps


def frames_info(src: str) -> int:
    """video total frames lookup"""
    video = cv2.VideoCapture(src)
    frame_count = 0
    while True:
        ret, frame = video.read()
        if ret is False:
            break
        frame_count = frame_count + 1
    return frame_count



def video_extract(src: str, dst: str, thread: int) -> None:
    """pre-processing video to png"""
    cmd = (
        f"ffmpeg -y -hide_banner -loglevel warning "
        f"-threads {thread} "
        f"-i {src} "
        f"-map 0:a? /tmp/audio.m4a "
        f"{dst}/%8d.png"
    )
    print(cmd)
    os.system(cmd)
    print("The video-image extracting job is done.")

def video_fusion(src: str, dst: str, fps: float, thread: int, bitrate: str) -> None:
    """post-processing png to video"""
    cmd = (
        f"ffmpeg -y -hide_banner -loglevel warning "
        f"-threads {thread} "
        f"-r {fps} "
        f"-f image2 -i {src} "
        f"-i /tmp/audio.m4a "
        f"-y -c:v libx264 -pix_fmt yuv420p -preset slow -crf 18 -profile:v baseline -b:v {bitrate} -minrate {bitrate} -maxrate {bitrate} -bufsize 6M -c:a aac {dst}"
    )
    print(cmd)
    os.system(cmd)
    print("The image-video fusion job is done.")

