import os
import requests
import datetime
import random
import string
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# 从环境变量读取敏感信息（推荐）或写死（仅测试）
COOKIE = os.getenv("KK_COOKIE", "你的Cookie字符串")
TOKEN_URL = "https://author.kuaikanmanhua.com/v1/graph/pc/partner/qiniuUploadToken?type=3"
UPLOAD_URL = "https://upload.qiniup.com/"

def get_upload_token() -> str:
    """第一步：获取七牛上传 token"""
    headers = {
        "User-Agent": "Mozilla/5.0 ...",  # 同上
        "Referer": "https://author.kuaikanmanhua.com/?trigger_btn=我要投稿",
        "Cookie": COOKIE,
    }
    resp = requests.get(TOKEN_URL, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="获取上传 token 失败")
    data = resp.json()
    return data["data"]["token"]

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # 1. 获取 token
    token = get_upload_token()

    # 2. 构造 key（保持原来的规则：日期/随机名.扩展名）
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    key = f"image/{date_str}/{random_name}.{ext}"

    # 3. 上传到七牛
    files = {"file": (file.filename, file.file, file.content_type)}
    data = {"token": token, "key": key}
    headers = {
        "User-Agent": "Mozilla/5.0 ...",
        "Origin": "https://author.kuaikanmanhua.com",
        "Referer": "https://author.kuaikanmanhua.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }
    resp = requests.post(UPLOAD_URL, files=files, data=data, headers=headers)

    if resp.status_code == 200:
        image_url = f"https://tncache1-f1.v3mh.com/{key}"
        return JSONResponse({
            "success": True,
            "url": image_url,
            "key": key,
        })
    else:
        raise HTTPException(status_code=502, detail=f"上传失败: {resp.text}")