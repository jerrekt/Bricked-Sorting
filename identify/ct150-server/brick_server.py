from flask import Flask, Response, request, jsonify, render_template_string, send_from_directory
import requests
import sqlite3
from pathlib import Path

from classify import (
    COLORS, COLOR_LABELS, SHAPES,
    bin_position, choose_color_bucket, choose_shape, get_bin_id,
)

app = Flask(__name__)

BRICKOGNIZE_URL = "https://api.brickognize.com/predict/parts/"
DB_PATH = Path(__file__).with_name("sort_history.db")
SAVE_DIR = Path("/opt/bricked-sorting/scanned_images")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR = Path("/opt/bricked-sorting/static")
BRICKBASE_URL = "http://127.0.0.1:8080"
CAMERA_STREAM_URL = "http://<PI_TAILNET_IP>:8001/stream"
CAMERA_SNAPSHOT_URL = "http://<PI_TAILNET_IP>:8001/snapshot"

# 16 bins = 2 shapes x 8 color families (see classify.py), e.g. BRICK_RED
BIN_KEYS = [get_bin_id(shape, color) for shape in SHAPES for color in COLORS]

# Status-LED color sent to the Pi as "rgb", one per color family
COLOR_RGB = {
    "RED": [255, 0, 0],
    "YELLOW": [255, 255, 0],
    "GREEN": [0, 255, 0],
    "BLUE": [0, 0, 255],
    "BROWN": [139, 69, 19],
    "BLACK": [40, 40, 40],
    "WHITE": [255, 255, 255],
    "SPECIAL": [145, 0, 220],
}

# Color-family rows for the old "/" page: (bucket, slot number, label, rgb)
BIN_CONFIGURATION = [
    (color, slot + 1, COLOR_LABELS[color], COLOR_RGB[color])
    for slot, color in enumerate(COLORS)
]


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def setup_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scanned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            name TEXT NOT NULL,
            part_id TEXT,
            category TEXT,
            shape TEXT,
            color TEXT,
            color_bucket TEXT,
            bin_number INTEGER,
            confidence REAL,
            color_confidence REAL
        )
    """)

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(scans)").fetchall()
    }

    if "image_filename" not in columns:
        connection.execute("ALTER TABLE scans ADD COLUMN image_filename TEXT")

    # The "bin" key returned to the Pi, e.g. BRICK_RED. Older rows stay NULL.
    if "bin_name" not in columns:
        connection.execute("ALTER TABLE scans ADD COLUMN bin_name TEXT")

    connection.commit()
    connection.close()


def save_scan_image(image_bytes, bin_name):
    """Save the JPEG for the Live Scan Feed."""
    timestamp = int(__import__("time").time() * 1000)
    safe_bin_name = "".join(
        character if character.isalnum() or character in "_-"
        else "_"
        for character in bin_name
    )

    filename = f"{timestamp}_{safe_bin_name}.jpg"
    image_path = SAVE_DIR / filename

    with open(image_path, "wb") as image_file:
        image_file.write(image_bytes)

    return filename



def cleanup_old_scan_images(keep=6):
    """Keep only the newest saved camera captures."""
    images = sorted(
        SAVE_DIR.glob("*.jpg"),
        key=lambda image_path: image_path.stat().st_mtime,
        reverse=True,
    )

    for old_image in images[keep:]:
        old_image.unlink(missing_ok=True)


def save_scan(result):
    """Save one successful LEGO identification to the history database."""
    connection = get_db()

    connection.execute(
        """
        INSERT INTO scans (
            name, part_id, category, shape, color, color_bucket,
            bin_number, confidence, color_confidence, image_filename,
            bin_name
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["name"],
            result["part_id"],
            result["category"],
            result["shape"],
            result["color"],
            result["color_bucket"],
            result["bin_number"],
            result["confidence"],
            result["color_confidence"],
            result.get("image_filename"),
            result.get("bin"),
        ),
    )

    connection.commit()
    connection.close()




@app.route("/api/calibrate-background", methods=["POST"])
def calibrate_background():
    return jsonify({
        "ok": False,
        "message": "Calibration is disabled until YOLO is installed"
    }), 409


@app.route("/api/detect-boxes", methods=["POST"])
def detect_boxes():
    return jsonify({
        "boxes": [],
        "detector": "disabled",
        "message": "YOLO detector has not been installed yet"
    })

@app.route("/identify", methods=["POST"])
def identify():
    preview = request.args.get("preview") == "1"
    if "image" not in request.files:
        return jsonify({"error": "No image received"}), 400

    image = request.files["image"]
    image_bytes = image.read()

    if not image_bytes:
        return jsonify({"error": "Empty image received"}), 400

    try:
        response = requests.post(
            BRICKOGNIZE_URL,
            params={
                "top_k_items": 3,
                "predict_color": "true",
                "top_k_colors": 3,
            },
            files={
                "query_image": (
                    image.filename,
                    image_bytes,
                    image.mimetype or "image/jpeg",
                )
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        items = data.get("items", [])
        colors = data.get("colors", [])

        if colors:
            best_color = colors[0]
            color_name = best_color.get("name", "Unknown")
            color_confidence = round(best_color.get("score", 0) * 100, 1)
        else:
            color_name = "Unknown"
            color_confidence = 0

        # Unknown colors land in SPECIAL (classify.py), so every detected part has a bin.
        color_bucket = choose_color_bucket(color_name, color_confidence)

        if not items:
            result = {
                "name": "Unknown LEGO",
                "part_id": "Unknown",
                "category": "Unknown",
                "confidence": 0,
                "shape": "OTHER",
                "bin": "NO_LEGO",
                "bin_number": 0,
                "floor": None,
                "slot": None,
                "color": color_name,
                "color_bucket": color_bucket,
                "rgb": [0, 0, 0],
                "color_confidence": color_confidence,
                "lego_detected": False,
                "image_filename": None,
                "image_url": None,
            }

            print("No LEGO detected; ignoring image.", flush=True)
            return jsonify(result)

        best = items[0]
        name = best.get("name", "Unknown LEGO")
        category = best.get("category", "Unknown")
        confidence = round(best.get("score", 0) * 100, 1)

        # Preserve Brickognize detection coordinates for the camera overlay.
        box = (
            best.get("bounding_box")
            or best.get("bbox")
            or best.get("box")
            or data.get("bounding_box")
            or data.get("bbox")
        )

        shape = choose_shape(name, confidence)
        bin_name = get_bin_id(shape, color_bucket)
        floor, slot = bin_position(bin_name)
        bin_number = floor * 8 + slot + 1    # 1-8 bricks (bottom), 9-16 other (top)

        result = {
            "name": name,
            "part_id": best.get("id", "Unknown"),
            "category": category,
            "confidence": confidence,
            "shape": shape,
            "bin": bin_name,
            "bin_number": bin_number,
            "floor": floor,
            "slot": slot,
            "color": color_name,
            "color_bucket": color_bucket,
            "rgb": COLOR_RGB[color_bucket],
            "color_confidence": color_confidence,
            "box": box,
        }

        if preview:
            result["image_filename"] = None
            result["image_url"] = None
            return jsonify(result)

        image_filename = save_scan_image(image_bytes, bin_name)
        cleanup_old_scan_images(keep=6)
        result["image_filename"] = image_filename
        result["image_url"] = f"/scans/{image_filename}"
        save_scan(result)

        print("Result:", result, flush=True)
        return jsonify(result)

    except Exception as error:
        print("Error:", error, flush=True)
        return jsonify({"error": str(error)}), 500


@app.route("/scans/<filename>")
def scanned_image(filename):
    """Serve one saved scan image by its generated filename."""
    return send_from_directory(SAVE_DIR, filename)


@app.route("/api/live-feed")
def live_feed():
    """Return the newest saved scans for the dashboard Live Scan Feed."""
    connection = get_db()

    scans = connection.execute("""
        SELECT scanned_at, name, part_id, color, color_bucket,
               bin_number, confidence, image_filename
        FROM scans
        WHERE image_filename IS NOT NULL
        ORDER BY id DESC
        LIMIT 12
    """).fetchall()

    connection.close()

    return jsonify({
        "scans": [
            {
                **dict(scan),
                "image_url": f"/scans/{scan['image_filename']}",
            }
            for scan in scans
        ]
    })


# Both addresses work:
# http://<CT150_TAILNET_IP>:5000/health
# http://<CT150_TAILNET_IP>:5000/health-detail
@app.route("/health")
@app.route("/health-detail")
def health():
    health_status = {
        "server": {
            "ok": True,
            "message": "Inference server is running"
        },
        "brickognize": {
            "ok": False,
            "message": "Checking Brickognize API..."
        }
    }

    try:
        # Any HTTP response means the API server is reachable.
        response = requests.get(
            "https://api.brickognize.com",
            timeout=6
        )

        health_status["brickognize"] = {
            "ok": True,
            "message": f"Brickognize API reachable (HTTP {response.status_code})"
        }

        return jsonify(health_status), 200

    except requests.RequestException as error:
        health_status["brickognize"] = {
            "ok": False,
            "message": f"Brickognize API error: {error}"
        }

        return jsonify(health_status), 503


@app.route("/old-dashboard")
def dashboard():
    connection = get_db()

    total_pieces = connection.execute(
        "SELECT COUNT(*) FROM scans"
    ).fetchone()[0]

    latest = connection.execute("""
        SELECT scanned_at, name, color, color_bucket, bin_number, confidence
        FROM scans
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    color_counts = {
        row["color_bucket"]: row["total"]
        for row in connection.execute("""
            SELECT color_bucket, COUNT(*) AS total
            FROM scans
            GROUP BY color_bucket
        """).fetchall()
    }

    piece_counts = connection.execute("""
        SELECT name, COUNT(*) AS total
        FROM scans
        GROUP BY name
        ORDER BY total DESC, name ASC
        LIMIT 8
    """).fetchall()

    recent_scans = connection.execute("""
        SELECT scanned_at, name, color, bin_number, confidence
        FROM scans
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()

    connection.close()

    color_rows = []
    maximum = max(color_counts.values(), default=1)

    for bucket, number, label, rgb in BIN_CONFIGURATION:
        count = color_counts.get(bucket, 0)

        color_rows.append({
            "number": number,
            "label": label,
            "count": count,
            "rgb": f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})",
            "percent": round((count / maximum) * 100),
        })

    return render_template_string(
        DASHBOARD_HTML,
        total_pieces=total_pieces,
        latest=latest,
        colors=color_rows,
        pieces=piece_counts,
        recent=recent_scans,
    )


DASHBOARD_HTML = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="5">
    <title>Bricked Sorting Dashboard</title>
    <style>
        body {
            background: #101827;
            color: #eef4ff;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 28px;
        }

        h1 {
            margin-bottom: 4px;
        }

        .sub {
            color: #9eb0cc;
            margin-top: 0;
        }

        .cards, .grid {
            display: grid;
            gap: 16px;
        }

        .cards {
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            margin: 22px 0;
        }

        .grid {
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
        }

        .card {
            background: #1b2739;
            border-radius: 12px;
            padding: 18px;
        }

        .number {
            color: #6dd5fa;
            font-size: 40px;
            font-weight: bold;
            margin: 8px 0;
        }

        .color-row {
            margin: 14px 0;
        }

        .bar-bg {
            background: #303f55;
            border-radius: 8px;
            height: 18px;
            overflow: hidden;
        }

        .bar {
            height: 100%;
            min-width: 2px;
        }

        table {
            border-collapse: collapse;
            width: 100%;
        }

        th, td {
            border-bottom: 1px solid #32445e;
            padding: 10px 6px;
            text-align: left;
        }

        th {
            color: #9eb0cc;
        }

        .latest {
            color: #7ee787;
            font-size: 20px;
        }

        .muted {
            color: #9eb0cc;
        }
    </style>
</head>

<body>
    <h1>🧱 Bricked Sorting Dashboard</h1>
    <p class="sub">Updates automatically every 5 seconds</p>

    <div class="cards">
        <div class="card">
            <div class="muted">Total LEGO Pieces Sorted</div>
            <div class="number">{{ total_pieces }}</div>
        </div>

        <div class="card">
            <div class="muted">Latest Detection</div>

            {% if latest %}
                <p class="latest">{{ latest["name"] }}</p>
                <p>{{ latest["color"] }} → Bin {{ latest["bin_number"] }}</p>
                <p class="muted">{{ latest["confidence"] }}% confidence</p>
            {% else %}
                <p class="muted">No pieces have been sorted yet.</p>
            {% endif %}
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Pieces by Physical Bin</h2>

            {% for color in colors %}
                <div class="color-row">
                    <strong>Bin {{ color["number"] }} — {{ color["label"] }}</strong>
                    <span class="muted">({{ color["count"] }})</span>

                    <div class="bar-bg">
                        <div class="bar"
                             style="width: {{ color["percent"] }}%; background: {{ color["rgb"] }};">
                        </div>
                    </div>
                </div>
            {% endfor %}
        </div>

        <div class="card">
            <h2>Most Common LEGO Pieces</h2>

            {% if pieces %}
                <table>
                    <tr>
                        <th>LEGO Piece</th>
                        <th>Count</th>
                    </tr>

                    {% for piece in pieces %}
                        <tr>
                            <td>{{ piece["name"] }}</td>
                            <td>{{ piece["total"] }}</td>
                        </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p class="muted">Waiting for the first scan.</p>
            {% endif %}
        </div>

        <div class="card">
            <h2>Last 10 Scans</h2>

            {% if recent %}
                <table>
                    <tr>
                        <th>Time</th>
                        <th>Piece</th>
                        <th>Bin</th>
                    </tr>

                    {% for scan in recent %}
                        <tr>
                            <td>{{ scan["scanned_at"] }}</td>
                            <td>{{ scan["name"] }}</td>
                            <td>Bin {{ scan["bin_number"] }} — {{ scan["color"] }}</td>
                        </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p class="muted">No scans saved yet.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


@app.route("/api/live-feed/clear", methods=["POST"])
def clear_live_feed_images():
    """Delete saved Live Scan Feed photos only; keep all scan/count data."""
    deleted = 0

    for image_file in SAVE_DIR.glob("*.jpg"):
        try:
            image_file.unlink()
            deleted += 1
        except OSError as error:
            print("Could not delete image:", image_file.name, error, flush=True)

    connection = get_db()
    connection.execute(
        "UPDATE scans SET image_filename = NULL WHERE image_filename IS NOT NULL"
    )
    connection.commit()
    connection.close()

    print(f"Live Scan Feed cleared: {deleted} images deleted.", flush=True)
    return jsonify({
        "ok": True,
        "deleted_images": deleted,
        "message": "Live Scan Feed images cleared. Scan records were kept."
    })




@app.route("/api/live-camera-snapshot")
def live_camera_snapshot():
    try:
        response = requests.get(CAMERA_SNAPSHOT_URL, timeout=10)
        response.raise_for_status()

        return Response(
            response.content,
            mimetype=response.headers.get("Content-Type", "image/jpeg"),
            headers={"Cache-Control": "no-store"}
        )
    except requests.RequestException as error:
        return jsonify({"error": str(error)}), 502

@app.route("/api/live-camera")
def live_camera():
    """Relay the Raspberry Pi MJPEG stream through this public server."""
    try:
        upstream = requests.get(
            CAMERA_STREAM_URL,
            stream=True,
            timeout=(5, 15),
        )
        upstream.raise_for_status()

        content_type = upstream.headers.get(
            "Content-Type",
            "multipart/x-mixed-replace; boundary=frame",
        )

        def generate():
            try:
                for chunk in upstream.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            finally:
                upstream.close()

        return Response(
            generate(),
            status=200,
            content_type=content_type,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate",
                "Pragma": "no-cache",
            },
        )

    except requests.RequestException as error:
        return jsonify({
            "ok": False,
            "error": str(error),
        }), 502



@app.route("/assets/<path:filename>")
def asset_file(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route("/")
@app.route("/dashboard")
def bins_dashboard():
    """16-bin dashboard page (also the bare URL)."""
    return send_from_directory(STATIC_DIR, "bins.html")


@app.route("/bins")
def bin_counts():
    """Pieces ever sorted into each of the 16 bins (new BRICK_RED-style names only)."""
    placeholders = ",".join("?" for _ in BIN_KEYS)
    connection = get_db()

    rows = connection.execute(
        f"""
        SELECT bin_name, COUNT(*) AS total
        FROM scans
        WHERE bin_name IN ({placeholders})
        GROUP BY bin_name
        """,
        BIN_KEYS,
    ).fetchall()

    connection.close()

    counts = {key: 0 for key in BIN_KEYS}
    counts.update({row["bin_name"]: row["total"] for row in rows})
    return jsonify(counts)


@app.route("/recent")
def recent_scans():
    """Newest 12 scans for the dashboard's Recent scans strip."""
    connection = get_db()

    scans = connection.execute("""
        SELECT name, bin_name, confidence, image_filename, scanned_at
        FROM scans
        ORDER BY id DESC
        LIMIT 12
    """).fetchall()

    connection.close()

    return jsonify([
        {
            "name": scan["name"],
            "bin": scan["bin_name"],
            "confidence": scan["confidence"],
            "image_url": (
                f"/scans/{scan['image_filename']}"
                if scan["image_filename"] else None
            ),
            # SQLite CURRENT_TIMESTAMP is UTC; mark it so browsers don't read it as local time.
            "created_at": scan["scanned_at"].replace(" ", "T") + "Z",
        }
        for scan in scans
    ])


@app.route("/tamper")
def tamper_status():
    """Bins whose lid switch was opened. No limit switches yet."""
    return jsonify([])


@app.route("/tamper/clear", methods=["POST"])
def tamper_clear():
    return jsonify({"ok": True})


@app.route("/api/parts")
@app.route("/api/sets")
def brickbase_proxy():
    """Pass Parts/Sets requests through to BrickBase so the dashboard needs no CORS."""
    try:
        response = requests.get(
            BRICKBASE_URL + request.full_path.rstrip("?"),
            timeout=30,
        )
    except requests.RequestException as error:
        return jsonify({"error": f"BrickBase unreachable: {error}"}), 502

    return Response(
        response.content,
        status=response.status_code,
        content_type=response.headers.get("Content-Type", "application/json"),
    )

setup_database()

print("Bricked Sorting server and dashboard started.", flush=True)
app.run(host="0.0.0.0", port=5000)
