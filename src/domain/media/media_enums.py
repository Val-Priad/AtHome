from enum import Enum


class MediaPurpose(str, Enum):
    estate = "estate"
    user_avatar = "user_avatar"


class MediaType(str, Enum):
    image = "image"
    video = "video"


class MediaContentType(str, Enum):
    jpeg = "image/jpeg"
    png = "image/png"
    webp = "image/webp"
    mp4 = "video/mp4"
