from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp as youtube_dl
import os
import uuid

router = APIRouter()

DOWNLOADS_DIR = "./downloads"


class VideoURL(BaseModel):
    url: str


def download_video(url: str, file_path: str):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": file_path,
        "merge_output_format": "mp4",
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


@router.post("/api/convert")
async def convert_video(video_url: VideoURL, background_tasks: BackgroundTasks):
    url = video_url.url
    if not youtube_dl.utils.url_or_none(url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    file_name = f"{uuid.uuid4()}.mp4"
    file_path = os.path.join(DOWNLOADS_DIR, file_name)

    background_tasks.add_task(download_video, url, file_path)

    return {"downloadUrl": f"http://localhost:8000/downloads/{file_name}"}


@router.get("/downloads/{file_name}")
async def get_download(file_name: str):
    file_path = os.path.join(DOWNLOADS_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4", filename=file_name)
    else:
        raise HTTPException(status_code=404, detail="File not found")
