from pathlib import Path

BASE_DIR=Path(__file__).resolve().parent
class Config:
    SECRET_KEY="dev-only-change-me"
    MAX_CONTENT_LENGTH=512*1024*1024
    OUTPUT_FOLDER=BASE_DIR/"static"/"outputs"
    ARABIC_FONT=BASE_DIR/"static"/"assets"/"NotoNaskhArabic-Regular.ttf"
