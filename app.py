import os, uuid, threading, time, json, re
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Store job status: { job_id: { status, progress, file, error, title, size } }
jobs = {}

# Auto-delete files after 2h
def auto_delete(path, delay=7200):
    def _del():
        time.sleep(delay)
        try: os.remove(path)
        except: pass
    threading.Thread(target=_del, daemon=True).start()

# ─────────────────────────────────────────────
#  yt-dlp progress hook
# ─────────────────────────────────────────────
def make_hook(job_id):
    def hook(d):
        j = jobs[job_id]
        if d["status"] == "downloading":
            pct = d.get("_percent_str", "0%").strip().replace("%","")
            try: j["progress"] = min(int(float(pct)), 99)
            except: pass
            j["speed"] = d.get("_speed_str","").strip()
            j["eta"]   = d.get("_eta_str","").strip()
            j["status"] = "downloading"
        elif d["status"] == "finished":
            j["progress"] = 99
            j["status"]   = "processing"
    return hook

# ─────────────────────────────────────────────
#  Detect platform from URL
# ─────────────────────────────────────────────
def detect_platform(url):
    u = url.lower()
    if "youtube.com" in u or "youtu.be" in u: return "youtube"
    if "spotify.com" in u:                     return "spotify"
    if "soundcloud.com" in u:                  return "soundcloud"
    if "tiktok.com" in u:                      return "tiktok"
    if "instagram.com" in u:                   return "instagram"
    if "twitter.com" in u or "x.com" in u:     return "twitter"
    if "facebook.com" in u or "fb.watch" in u: return "facebook"
    if "deezer.com" in u:                      return "deezer"
    return "generic"

# ─────────────────────────────────────────────
#  yt-dlp options builder
# ─────────────────────────────────────────────
def build_ydl_opts(job_id, fmt, quality, out_path_tmpl):
    postprocessors = []

    if fmt in ("mp3","aac","flac","wav","ogg","m4a","opus","wma","aiff","mp2","ac3"):
        # Audio only
        quality_map = {
            "320 kbps (Max)": "320", "320 kbps": "320",
            "256 kbps": "256", "192 kbps": "192", "128 kbps": "128",
            "FLAC Lossless": "0",
        }
        abr = quality_map.get(quality, "320")
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": fmt,
            "preferredquality": abr,
        })
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
        postprocessors.append({"key": "EmbedThumbnail"})
        return {
            "format": "bestaudio/best",
            "outtmpl": out_path_tmpl,
            "postprocessors": postprocessors,
            "writethumbnail": True,
            "progress_hooks": [make_hook(job_id)],
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
        }
    else:
        # Video
        quality_map = {
            "4K Ultra HD": "2160", "1080p Full HD": "1080",
            "Originale (HD)": "1080", "1080p": "1080",
            "720p HD": "720", "720p": "720",
            "480p": "480", "360p": "360",
        }
        height = quality_map.get(quality, "1080")
        vformat = f"bestvideo[height<={height}][ext={fmt}]+bestaudio/bestvideo[height<={height}]+bestaudio/best[height<={height}]"
        postprocessors.append({
            "key": "FFmpegVideoConvertor",
            "preferedformat": fmt,
        })
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
        return {
            "format": vformat,
            "outtmpl": out_path_tmpl,
            "postprocessors": postprocessors,
            "merge_output_format": fmt,
            "progress_hooks": [make_hook(job_id)],
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
        }

# ─────────────────────────────────────────────
#  Spotify via spotdl
# ─────────────────────────────────────────────
def download_spotify(job_id, url, fmt, quality):
    import subprocess, glob
    j = jobs[job_id]
    j["status"] = "downloading"
    quality_map = {"320 kbps (Max)": "320k","256 kbps":"256k","192 kbps":"192k","128 kbps":"128k","FLAC Lossless":"flac"}
    bitrate = quality_map.get(quality, "320k")
    out_dir = os.path.join(DOWNLOAD_DIR, job_id)
    os.makedirs(out_dir, exist_ok=True)
    cmd = ["spotdl", url, "--format", fmt if fmt != "flac" else "flac",
           "--bitrate", bitrate, "--output", out_dir, "--overwrite", "force"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        line = line.strip()
        if "Downloaded" in line or "%" in line:
            m = re.search(r"(\d+)%", line)
            if m: j["progress"] = int(m.group(1))
    proc.wait()
    files = glob.glob(os.path.join(out_dir, f"*.{fmt}")) + \
            glob.glob(os.path.join(out_dir, "*.flac")) + \
            glob.glob(os.path.join(out_dir, "*.mp3"))
    if not files:
        j["status"] = "error"; j["error"] = "Aucun fichier généré par spotdl"
        return
    # Zip if multiple files
    if len(files) > 1:
        import zipfile
        zip_path = os.path.join(DOWNLOAD_DIR, f"{job_id}.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for f in files: zf.write(f, os.path.basename(f))
        j["file"] = zip_path
        j["filename"] = "spotify_playlist.zip"
    else:
        j["file"] = files[0]
        j["filename"] = os.path.basename(files[0])
    j["progress"] = 100; j["status"] = "done"
    auto_delete(j["file"])

# ─────────────────────────────────────────────
#  Generic yt-dlp download
# ─────────────────────────────────────────────
def download_ytdlp(job_id, url, fmt, quality):
    j = jobs[job_id]
    out_tmpl = os.path.join(DOWNLOAD_DIR, f"{job_id}_%(title)s.%(ext)s")
    opts = build_ydl_opts(job_id, fmt, quality, out_tmpl)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise Exception("Impossible d'extraire les informations du lien")
            # Find the output file
            title = info.get("title", "fichier")
            j["title"] = title
            # Look for downloaded file
            import glob as g
            pattern = os.path.join(DOWNLOAD_DIR, f"{job_id}_*")
            files = g.glob(pattern)
            # Filter out thumbnails
            exts = (fmt, "mp4","mkv","webm","mp3","flac","wav","aac","m4a","ogg","zip")
            files = [f for f in files if f.split(".")[-1].lower() in exts]
            if not files:
                raise Exception("Fichier de sortie introuvable après conversion")
            j["file"] = files[0]
            j["filename"] = os.path.basename(files[0])
            sz = os.path.getsize(files[0])
            j["size"] = f"{sz/1024/1024:.1f} MB"
            j["progress"] = 100
            j["status"] = "done"
            auto_delete(files[0])
    except Exception as e:
        j["status"] = "error"
        j["error"] = str(e)

# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@app.route("/api/start", methods=["POST"])
def start():
    data = request.get_json()
    url     = (data.get("url") or "").strip()
    fmt     = (data.get("format") or "mp3").lower().strip()
    quality = data.get("quality") or "320 kbps (Max)"

    if not url:
        return jsonify({"error": "URL manquante"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "starting", "progress": 0, "file": None,
        "filename": None, "error": None, "title": "",
        "size": "", "speed": "", "eta": ""
    }

    platform = detect_platform(url)

    def run():
        if platform == "spotify":
            download_spotify(job_id, url, fmt, quality)
        else:
            download_ytdlp(job_id, url, fmt, quality)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id, "platform": platform})


@app.route("/api/status/<job_id>")
def status(job_id):
    j = jobs.get(job_id)
    if not j: return jsonify({"error": "Job introuvable"}), 404
    return jsonify({
        "status":   j["status"],
        "progress": j["progress"],
        "title":    j.get("title",""),
        "size":     j.get("size",""),
        "speed":    j.get("speed",""),
        "eta":      j.get("eta",""),
        "error":    j.get("error"),
        "filename": j.get("filename",""),
    })


@app.route("/api/download/<job_id>")
def download(job_id):
    j = jobs.get(job_id)
    if not j or j["status"] != "done":
        abort(404)
    path = j["file"]
    if not path or not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=j["filename"])


@app.route("/api/info", methods=["POST"])
def info():
    """Return metadata without downloading"""
    data = request.get_json()
    url = (data.get("url") or "").strip()
    if not url: return jsonify({"error": "URL manquante"}), 400
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title":     info.get("title",""),
                "uploader":  info.get("uploader",""),
                "duration":  info.get("duration",0),
                "thumbnail": info.get("thumbnail",""),
                "view_count":info.get("view_count",0),
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    print("\n🎵 MediaDrop backend démarré sur http://localhost:5000\n")
    app.run(debug=False, port=5000, threaded=True)
