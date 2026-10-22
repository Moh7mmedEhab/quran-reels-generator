import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import pytest
import urllib.error
import urllib.request

from app import create_app


class ImageConfig:
    TESTING = True
    SECRET_KEY = "test"
    OUTPUT_FOLDER = None
    RENDER_JOBS_INLINE = True


def test_image_page_has_only_prompt_and_format_inputs_and_handles_missing_comfyui(monkeypatch, tmp_path):
    monkeypatch.delenv("COMFYUI_BASE_URL", raising=False)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(
        urllib.error.URLError("not running")))
    ImageConfig.OUTPUT_FOLDER = tmp_path
    client = create_app(ImageConfig).test_client()
    image_page=client.get("/images")
    assert image_page.status_code == 200
    assert b'id="prompt"' in image_page.data
    assert b'name="ratio"' in image_page.data
    assert image_page.data.count(b'name="provider"') == 2
    assert b'value="comfyui" checked' in image_page.data
    assert b'value="pollinations"' in image_page.data
    assert b'name="pollinations-mode"' in image_page.data
    assert b'value="keyless" checked' in image_page.data
    assert b'value="api"' in image_page.data
    assert b'id="pollinations-model"' in image_page.data
    assert b'No API key' in image_page.data
    assert b'id="style"' not in image_page.data
    assert b'id="lighting"' not in image_page.data
    assert b'id="quran"' not in image_page.data
    assert b"Gemini" not in image_page.data
    assert b"gallery-search" not in image_page.data
    assert b"gallery-ratio" not in image_page.data
    assert b"gallery-sort" not in image_page.data
    assert b"No generated images yet" in image_page.data
    assert client.get("/api/images").json["images"] == []
    assert b"AI generated backgrounds" in client.get("/").data
    missing = client.post("/api/images/generate", json={"prompt":"a quiet lake"})
    assert missing.status_code == 503
    assert "Start ComfyUI" in missing.json["error"]
    assert client.post("/api/images/generate", json={"prompt":"", "ratio":"9:16"}).status_code == 400


def test_second_concurrent_generation_is_rejected_without_calling_comfyui(monkeypatch, tmp_path):
    import app.routes as routes
    ImageConfig.OUTPUT_FOLDER=tmp_path
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfyui.invalid")
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: pytest.fail("ComfyUI should not be called"))
    client=create_app(ImageConfig).test_client()
    routes._IMAGE_GENERATION_LOCK.acquire()
    try:
        response=client.post("/api/images/generate",json={"prompt":"a sky","ratio":"1:1"})
    finally:
        routes._IMAGE_GENERATION_LOCK.release()
    assert response.status_code==429
    assert "already being generated" in response.json["error"]


def test_comfyui_http_error_is_actionable(monkeypatch, tmp_path):
    ImageConfig.OUTPUT_FOLDER=tmp_path
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfyui.invalid")
    monkeypatch.setattr(urllib.request,"urlopen",lambda *args,**kwargs:(_ for _ in ()).throw(
        urllib.error.HTTPError("http://comfyui.invalid/prompt",400,"bad workflow","",None)))
    response=create_app(ImageConfig).test_client().post("/api/images/generate",json={"prompt":"a sky"})
    assert response.status_code==502
    assert "checkpoint" in response.json["error"]


def test_pollinations_requires_server_key_without_calling_service(monkeypatch, tmp_path):
    ImageConfig.OUTPUT_FOLDER=tmp_path
    monkeypatch.delenv("POLLINATIONS_API_KEY", raising=False)
    monkeypatch.setattr(urllib.request,"urlopen",lambda *args,**kwargs:pytest.fail("Pollinations should not be called without a key"))
    response=create_app(ImageConfig).test_client().post("/api/images/generate",json={
        "prompt":"a quiet lake", "ratio":"9:16", "provider":"pollinations",
    })
    assert response.status_code==503
    assert "POLLINATIONS_API_KEY" in response.json["error"]


def test_pollinations_model_catalog_uses_live_image_models_and_hides_key(monkeypatch, tmp_path):
    import app.routes as routes
    ImageConfig.OUTPUT_FOLDER=tmp_path
    monkeypatch.setenv("POLLINATIONS_API_KEY", "private-model-key")
    monkeypatch.setattr(routes, "_POLLINATIONS_MODEL_CACHE", {"expires": 0.0, "models": []})
    catalog=[
        {"name":"black-forest-labs/flux.1-schnell", "aliases":["flux"], "category":"image",
         "title":"Flux Schnell", "publisher":"Black Forest Labs", "output_modalities":["image"],
         "supported_endpoints":["/image/{prompt}"], "pricing":{"currency":"pollen","completionImage":"0.01"}},
        {"name":"video/example", "category":"video", "output_modalities":["video"],
         "supported_endpoints":["/video/{prompt}"]},
    ]
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): return False
        def read(self,size=-1): return json.dumps(catalog).encode()
    captured=[]
    def fake_urlopen(req,timeout):
        captured.append(req)
        return Response()
    monkeypatch.setattr(urllib.request,"urlopen",fake_urlopen)
    response=create_app(ImageConfig).test_client().get("/api/images/models")
    assert response.status_code==200
    assert [model["name"] for model in response.json["models"]]==["black-forest-labs/flux.1-schnell"]
    assert response.json["models"][0]["aliases"]==["flux"]
    assert response.json["models"][0]["publisher"]=="Black Forest Labs"
    assert response.json["default_model"]=="black-forest-labs/flux.1-schnell"
    assert captured[0].get_header("Authorization")=="Bearer private-model-key"
    assert "private-model-key" not in response.get_data(as_text=True)


def test_pollinations_uses_exact_prompt_and_saves_selected_format(monkeypatch, tmp_path):
    ImageConfig.OUTPUT_FOLDER=tmp_path
    monkeypatch.setenv("POLLINATIONS_API_KEY","test-server-key")
    monkeypatch.setenv("POLLINATIONS_IMAGE_MODEL","black-forest-labs/flux.1-schnell")
    image=BytesIO(); Image.new("RGB",(576,1024),"teal").save(image,"PNG")
    generated_bytes=image.getvalue()
    captured=[]

    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): return False
        def read(self,size=-1): return generated_bytes if size < 0 else generated_bytes[:size]

    def fake_urlopen(req,timeout):
        captured.append((req,timeout))
        return Response()

    monkeypatch.setattr(urllib.request,"urlopen",fake_urlopen)
    user_prompt="misty lake, no writing or books"
    response=create_app(ImageConfig).test_client().post("/api/images/generate",json={
        "prompt":user_prompt, "ratio":"9:16", "provider":"pollinations",
        "model":"black-forest-labs/flux.2-pro",
    })
    assert response.status_code==200
    metadata=response.json
    assert metadata["provider"]=="pollinations"
    assert metadata["model"]=="Pollinations · black-forest-labs/flux.2-pro"
    assert metadata["generation_prompt"]==user_prompt
    assert (metadata["width"],metadata["height"])==(576,1024)
    assert (tmp_path/"generated-images"/metadata["filename"]).read_bytes()==generated_bytes
    req,timeout=captured[0]
    from urllib.parse import parse_qs, urlparse, unquote
    parsed=urlparse(req.full_url)
    assert parsed.scheme=="https" and parsed.netloc=="gen.pollinations.ai"
    assert unquote(parsed.path.removeprefix("/image/"))==user_prompt
    assert parse_qs(parsed.query)=={"model":["black-forest-labs/flux.2-pro"],"width":["576"],"height":["1024"]}
    assert req.get_header("Authorization")=="Bearer test-server-key"
    assert timeout==300
    assert "test-server-key" not in response.get_data(as_text=True)


def test_pollinations_legacy_generates_without_api_key(monkeypatch, tmp_path):
    ImageConfig.OUTPUT_FOLDER=tmp_path
    monkeypatch.delenv("POLLINATIONS_API_KEY", raising=False)
    image=BytesIO(); Image.new("RGB",(1024,576),"teal").save(image,"PNG")
    generated_bytes=image.getvalue()
    captured=[]
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): return False
        def read(self,size=-1): return generated_bytes if size < 0 else generated_bytes[:size]
    def fake_urlopen(req,timeout):
        captured.append((req,timeout))
        return Response()
    monkeypatch.setattr(urllib.request,"urlopen",fake_urlopen)
    user_prompt="a quiet night sky, no writing"
    response=create_app(ImageConfig).test_client().post("/api/images/generate",json={
        "prompt":user_prompt,"ratio":"16:9","provider":"pollinations_legacy","model":"zimage",
    })
    assert response.status_code==200
    metadata=response.json
    assert metadata["provider"]=="pollinations_legacy"
    assert metadata["model"]=="Pollinations (no API key) · zimage"
    assert metadata["generation_prompt"]==user_prompt
    assert (metadata["width"],metadata["height"])==(1024,576)
    req,timeout=captured[0]
    from urllib.parse import parse_qs, urlparse, unquote
    parsed=urlparse(req.full_url)
    assert parsed.scheme=="https" and parsed.netloc=="image.pollinations.ai"
    assert unquote(parsed.path.removeprefix("/prompt/"))==user_prompt
    assert parse_qs(parsed.query)=={"model":["zimage"],"width":["1024"],"height":["576"]}
    assert req.get_header("Authorization") is None
    assert timeout==300


def test_pollinations_legacy_rejects_unknown_model(monkeypatch, tmp_path):
    ImageConfig.OUTPUT_FOLDER=tmp_path
    monkeypatch.setattr(urllib.request,"urlopen",lambda *args,**kwargs:pytest.fail("invalid model must not call Pollinations"))
    response=create_app(ImageConfig).test_client().post("/api/images/generate",json={
        "prompt":"a quiet sky","provider":"pollinations_legacy","model":"black-forest-labs/flux.2-pro",
    })
    assert response.status_code==502
    assert "flux, zimage, or klein" in response.json["error"]


def test_unknown_generation_provider_is_rejected(tmp_path):
    ImageConfig.OUTPUT_FOLDER=tmp_path
    response=create_app(ImageConfig).test_client().post("/api/images/generate",json={
        "prompt":"a quiet lake", "provider":"unknown",
    })
    assert response.status_code==400


def test_comfyui_rejection_does_not_save_an_image(monkeypatch, tmp_path):
    ImageConfig.OUTPUT_FOLDER=tmp_path
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfyui.invalid")
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): return False
        def read(self): return json.dumps({"node_errors":{"1": {"errors": []}}}).encode()
    monkeypatch.setattr(urllib.request,"urlopen",lambda *args,**kwargs:Response())
    response=create_app(ImageConfig).test_client().post("/api/images/generate",json={"prompt":"a sky"})
    assert response.status_code==502
    assert "checkpoint" in response.json["error"]
    assert not (tmp_path/"generated-images").exists()


def test_gallery_image_download_and_delete_are_id_scoped(tmp_path):
    ImageConfig.OUTPUT_FOLDER = tmp_path
    folder = tmp_path / "generated-images"
    folder.mkdir()
    image_id = "a" * 32
    Image.new("RGB", (12, 20), "navy").save(folder / f"{image_id}.png")
    (folder / f"{image_id}.json").write_text(json.dumps({
        "id": image_id, "prompt": "night sky", "ratio": "9:16", "width": 12,
        "height": 20, "mime_type": "image/png", "filename": f"{image_id}.png",
        "created_at": "2026-10-22T00:00:00+03:00", "model": "test-model",
    }))
    client = create_app(ImageConfig).test_client()
    assert len(client.get("/api/images").json["images"]) == 1
    download = client.get(f"/api/images/{image_id}/file?download=1")
    assert download.status_code == 200 and download.mimetype == "image/png"
    assert client.get("/api/images/../file").status_code in (400, 404)
    assert client.delete(f"/api/images/{image_id}").json == {"ok": True}
    assert client.get(f"/api/images/{image_id}/file").status_code == 404


def test_metadata_cannot_redirect_image_file_access_outside_storage(tmp_path):
    ImageConfig.OUTPUT_FOLDER=tmp_path
    folder=tmp_path/"generated-images";folder.mkdir()
    image_id="d"*32
    outside=tmp_path/"private.txt";outside.write_text("private")
    (folder/f"{image_id}.json").write_text(json.dumps({
        "id":image_id,"prompt":"x","mime_type":"image/png","filename":"../private.txt",
    }))
    client=create_app(ImageConfig).test_client()
    assert client.get(f"/api/images/{image_id}/file").status_code==404
    assert client.delete(f"/api/images/{image_id}").status_code==404
    assert outside.read_text()=="private"


@pytest.mark.parametrize(("ratio", "dimensions"), [
    ("9:16", (576, 1024)), ("16:9", (1024, 576)), ("1:1", (768, 768)),
])
def test_comfyui_image_is_validated_saved_and_uses_expected_dimensions(monkeypatch, tmp_path, ratio, dimensions):
    ImageConfig.OUTPUT_FOLDER = tmp_path
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfyui.local:8188")
    monkeypatch.setenv("COMFYUI_CHECKPOINT", "test-model.safetensors")
    monkeypatch.setenv("COMFYUI_TIMEOUT_SECONDS", "5")
    monkeypatch.setenv("COMFYUI_POLL_INTERVAL_SECONDS", "0.1")
    image = BytesIO()
    Image.new("RGB", dimensions, "teal").save(image, format="PNG")
    generated_bytes = image.getvalue()

    class Response:
        def __init__(self, body): self.body = body
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size=-1): return self.body if size < 0 else self.body[:size]

    captured = []
    def fake_urlopen(req, timeout):
        captured.append(req)
        if req.full_url.endswith("/prompt"):
            return Response(json.dumps({"prompt_id": "prompt-123"}).encode())
        if "/history/prompt-123" in req.full_url:
            history = {"prompt-123": {"outputs": {"7": {"images": [
                {"filename": "quran-reels_00001_.png", "subfolder": "", "type": "output"},
            ]}}}}
            return Response(json.dumps(history).encode())
        if "/view?" in req.full_url:
            return Response(generated_bytes)
        raise AssertionError(req.full_url)
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    client = create_app(ImageConfig).test_client()
    generated = client.post("/api/images/generate", json={"prompt":"quiet sea","ratio":ratio})
    assert generated.status_code == 200
    metadata = generated.json
    assert (metadata["width"], metadata["height"], metadata["mime_type"]) == (*dimensions, "image/png")
    assert (tmp_path / "generated-images" / metadata["filename"]).read_bytes() == generated_bytes
    workflow_request = json.loads(captured[0].data)
    workflow = workflow_request["prompt"]
    assert workflow["1"]["inputs"]["ckpt_name"] == "test-model.safetensors"
    assert workflow["4"]["inputs"] == {"width": dimensions[0], "height": dimensions[1], "batch_size": 1}
    assert "quiet sea" in workflow["2"]["inputs"]["text"]
    assert workflow["2"]["inputs"]["text"] == "quiet sea"
    assert workflow["3"]["inputs"]["text"] == ""
    assert captured[0].full_url == "http://comfyui.local:8188/prompt"
    assert "/history/prompt-123" in captured[1].full_url
    assert "/view?" in captured[2].full_url
    assert metadata["model"] == "ComfyUI · test-model.safetensors"
    assert metadata["user_prompt"] == "quiet sea"
    assert "GEMINI_API_KEY" not in generated.get_data(as_text=True)


def test_saved_generated_image_can_enter_existing_video_export_pipeline(monkeypatch, tmp_path):
    import app.routes as routes
    ImageConfig.OUTPUT_FOLDER = tmp_path / "outputs"
    folder=ImageConfig.OUTPUT_FOLDER / "generated-images"
    folder.mkdir(parents=True)
    image_id="b" * 32
    image=BytesIO(); Image.new("RGB", (64, 96), "midnightblue").save(image, "PNG")
    image_bytes=image.getvalue()
    (folder / f"{image_id}.png").write_bytes(image_bytes)
    (folder / f"{image_id}.json").write_text(json.dumps({
        "id":image_id,"prompt":"quiet night sky","ratio":"9:16","width":64,"height":96,
        "mime_type":"image/png","filename":f"{image_id}.png","model":"test","created_at":"2026-10-22T00:00:00+03:00",
    }))
    recitation=tmp_path / "recitation.mp3"; recitation.write_bytes(b"audio")
    seen={}
    def fake_render(**kwargs):
        seen["background"] = Path(kwargs["background_path"]).read_bytes()
        Path(kwargs["output_path"]).write_bytes(b"complete-mp4" * 200)
        return {"path":str(kwargs["output_path"]),"duration":4,"width":1080,"height":1920}
    monkeypatch.setattr(routes,"download_recitation",lambda *args,**kwargs:SimpleNamespace(path=recitation,start=0,end=4,ayah_durations=[4]))
    monkeypatch.setattr(routes,"render_reel",fake_render)
    monkeypatch.setattr(routes,"validate_rendered_output",lambda *args,**kwargs:{"playable":True})
    client=create_app(ImageConfig).test_client()
    image_download=client.get(f"/api/images/{image_id}/file")
    assert image_download.status_code==200 and image_download.mimetype=="image/png"
    export=client.post("/api/generate",data={
        "surah":"55","ayah_start":"13","ayah_end":"13","aspect_ratio":"9:16",
        "reciter_id":"mishary_alafasy","background":(BytesIO(image_download.data),"selected-ai-image.png","image/png"),
    },content_type="multipart/form-data")
    assert export.status_code==202, export.json
    assert seen["background"]==image_bytes
    assert client.get(export.json["status_url"]).json["status"]=="complete"


def test_saved_ai_background_is_visible_in_a_real_rendered_mp4(monkeypatch, tmp_path):
    import math
    import wave
    import numpy as np
    from moviepy import VideoFileClip
    import app.routes as routes
    ImageConfig.OUTPUT_FOLDER=tmp_path / "outputs"
    folder=ImageConfig.OUTPUT_FOLDER / "generated-images";folder.mkdir(parents=True)
    image_id="c" * 32
    source=Image.new("RGB",(180,320),(12,42,142));image=BytesIO();source.save(image,"PNG");image_bytes=image.getvalue()
    (folder/f"{image_id}.png").write_bytes(image_bytes)
    (folder/f"{image_id}.json").write_text(json.dumps({
        "id":image_id,"prompt":"blue night sky","ratio":"9:16","width":180,"height":320,
        "mime_type":"image/png","filename":f"{image_id}.png","model":"test","created_at":"2026-10-22T00:00:00+03:00",
    }))
    audio_path=tmp_path/"tone.wav";rate=44100;duration=2
    times=np.arange(rate*duration,dtype=np.float64)/rate
    samples=(.12*np.sin(2*math.pi*330*times)*32767).astype("int16")
    with wave.open(str(audio_path),"wb") as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(rate);output.writeframes(samples.tobytes())
    monkeypatch.setattr(routes,"download_recitation",lambda *args,**kwargs:SimpleNamespace(path=audio_path,start=0,end=duration,ayah_durations=[duration],word_timings=None,timing_note="test audio"))
    client=create_app(ImageConfig).test_client()
    stored=client.get(f"/api/images/{image_id}/file")
    result=client.post("/api/generate",data={
        "surah":"55","ayah_start":"13","ayah_end":"13","aspect_ratio":"9:16",
        "resolution":"480p","fps":"24","quality":"fast","encoder":"cpu",
        "reciter_id":"mishary_alafasy","show_quran_text":"false","show_surah_title":"false",
        "show_ayah_number":"false","viewer_title_enabled":"false","viewer_header_surah_enabled":"false",
        "viewer_header_range_enabled":"false","show_waveform":"false","show_reciter_badge":"false",
        "show_progress":"false","background_overlay_opacity":"0",
        "background":(BytesIO(stored.data),"ai-background.png","image/png"),
    },content_type="multipart/form-data")
    assert result.status_code==202,result.json
    job=client.get(result.json["status_url"]).json
    assert job["status"]=="complete",job
    rendered=client.get(job["result"]["download_url"])
    assert rendered.status_code==200 and rendered.mimetype=="video/mp4"
    path=ImageConfig.OUTPUT_FOLDER/job["result"]["filename"]
    clip=VideoFileClip(str(path))
    try:
        assert clip.size==[480,852]
        frame=clip.get_frame(.5)
        pixel=frame[426,240].astype(int)
        assert pixel[2] > pixel[0]*2 and pixel[2] > pixel[1]*1.5
    finally:
        clip.close()
