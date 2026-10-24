from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BRICKOGNIZE_URL = "https://api.brickognize.com/predict/parts/"

# Specific color names must be above general names such as "blue" and "green".
# The RGB values are for the physical RGB LED display.
COLOR_PATTERNS = [
    # Transparent LEGO colors
    ("trans clear", [255, 255, 255]),
    ("trans black", [40, 40, 40]),
    ("trans brown", [130, 70, 25]),
    ("trans dark blue", [0, 40, 150]),
    ("trans light blue", [80, 180, 255]),
    ("trans medium blue", [0, 100, 220]),
    ("trans neon green", [0, 255, 40]),
    ("trans bright green", [0, 255, 90]),
    ("trans green", [0, 200, 70]),
    ("trans neon orange", [255, 70, 0]),
    ("trans orange", [255, 91, 0]),
    ("trans yellow", [255, 255, 0]),
    ("trans dark pink", [220, 0, 100]),
    ("trans light purple", [190, 100, 255]),
    ("trans purple", [130, 0, 220]),
    ("trans pink", [255, 70, 160]),
    ("trans red", [255, 0, 0]),
    ("trans blue", [0, 0, 255]),

    # Gray, black, and white
    ("very light bluish gray", [220, 225, 225]),
    ("light bluish gray", [170, 180, 185]),
    ("dark bluish gray", [65, 75, 80]),
    ("very light gray", [225, 225, 225]),
    ("light gray", [180, 180, 180]),
    ("dark gray", [80, 80, 80]),
    ("bluish gray", [130, 140, 145]),
    ("gray", [130, 130, 130]),
    ("grey", [130, 130, 130]),
    ("white", [255, 255, 255]),
    ("black", [0, 0, 0]),

    # Reds, pinks, purples
    ("medium dark pink", [210, 0, 105]),
    ("bright pink", [255, 0, 140]),
    ("dark pink", [210, 0, 90]),
    ("rose pink", [255, 95, 160]),
    ("warm pink", [255, 120, 175]),
    ("light purple", [205, 120, 255]),
    ("dark purple", [75, 0, 125]),
    ("medium lavender", [170, 110, 200]),
    ("light lilac", [215, 170, 255]),
    ("medium violet", [130, 0, 210]),
    ("blue violet", [95, 0, 190]),
    ("light violet", [180, 100, 240]),
    ("violet", [120, 0, 220]),
    ("purple", [145, 0, 220]),
    ("lavender", [190, 145, 220]),
    ("lilac", [195, 135, 235]),
    ("magenta", [255, 0, 190]),
    ("pink", [255, 75, 160]),
    ("dark salmon", [190, 65, 55]),
    ("light salmon", [255, 145, 125]),
    ("salmon", [250, 115, 100]),
    ("sand red", [145, 80, 75]),
    ("coral", [255, 100, 90]),
    ("dark red", [115, 0, 0]),
    ("red", [255, 0, 0]),

    # Browns, tan, skin-tone colors
    ("medium nougat", [190, 115, 70]),
    ("dark nougat", [100, 55, 35]),
    ("light nougat", [255, 200, 155]),
    ("medium tan", [205, 170, 105]),
    ("dark tan", [150, 115, 60]),
    ("reddish brown", [110, 45, 20]),
    ("medium brown", [135, 75, 35]),
    ("light brown", [190, 120, 65]),
    ("dark brown", [70, 35, 15]),
    ("sienna", [160, 70, 30]),
    ("umber", [90, 55, 25]),
    ("nougat", [225, 150, 100]),
    ("brown", [125, 65, 25]),
    ("tan", [220, 185, 120]),

    # Orange and yellow
    ("bright light orange", [255, 190, 55]),
    ("very light orange", [255, 215, 145]),
    ("medium orange", [255, 125, 20]),
    ("light orange", [255, 175, 75]),
    ("neon orange", [255, 75, 0]),
    ("reddish orange", [230, 65, 0]),
    ("dark orange", [180, 55, 0]),
    ("warm yellowish orange", [255, 160, 45]),
    ("dark yellow", [175, 135, 0]),
    ("ochre yellow", [190, 145, 20]),
    ("bright light yellow", [255, 250, 135]),
    ("light yellow", [255, 240, 120]),
    ("neon yellow", [225, 255, 0]),
    ("orange", [255, 91, 0]),
    ("yellow", [255, 255, 0]),

    # Green and turquoise
    ("dark olive green", [55, 65, 10]),
    ("olive green", [105, 115, 20]),
    ("yellowish green", [135, 220, 30]),
    ("medium lime", [145, 230, 0]),
    ("light lime", [190, 255, 50]),
    ("neon green", [0, 255, 45]),
    ("bright green", [0, 255, 55]),
    ("medium green", [0, 165, 70]),
    ("light green", [100, 230, 100]),
    ("sand green", [80, 145, 115]),
    ("dark green", [0, 70, 25]),
    ("lime", [190, 255, 0]),
    ("green", [0, 255, 0]),

    ("dark turquoise", [0, 255, 170]),
    ("light turquoise", [55, 230, 205]),
    ("light aqua", [85, 235, 220]),
    ("turquoise", [0, 255, 170]),
    ("aqua", [0, 220, 210]),

    # Blue colors
    ("bright light blue", [130, 210, 255]),
    ("dark royal blue", [0, 35, 115]),
    ("dark azure", [0, 125, 200]),
    ("medium azure", [0, 170, 230]),
    ("maersk blue", [80, 175, 200]),
    ("sand blue", [75, 115, 150]),
    ("medium blue", [0, 100, 210]),
    ("light blue", [85, 175, 255]),
    ("sky blue", [90, 195, 255]),
    ("dark blue", [0, 30, 130]),
    ("royal blue", [0, 50, 190]),
    ("blue", [0, 0, 255]),

    # Metallic and special colors
    ("metallic silver", [185, 185, 195]),
    ("metallic gold", [210, 160, 25]),
    ("pearl gold", [190, 145, 25]),
    ("pearl dark gray", [70, 75, 80]),
    ("pearl light gray", [180, 185, 190]),
    ("chrome gold", [255, 195, 20]),
    ("chrome silver", [210, 210, 215]),
    ("glow in dark", [170, 255, 150])
]


def choose_bin(category, name):
    text = f"{category} {name}".lower()

    if "brick" in text:
        return "BRICK"
    elif "plate" in text:
        return "PLATE"
    elif "minifigure" in text or "minifig" in text:
        return "MINIFIGURE"
    else:
        return "OTHER"


def color_to_rgb(color_name):
    color_text = str(color_name).lower()
    color_text = color_text.replace("-", " ").replace("_", " ")

    for color_pattern, rgb in COLOR_PATTERNS:
        if color_pattern in color_text:
            return rgb

    return [0, 0, 0]


@app.route("/identify", methods=["POST"])
def identify():
    if "image" not in request.files:
        return jsonify({"error": "No image received"}), 400

    image = request.files["image"]

    try:
        response = requests.post(
            BRICKOGNIZE_URL,
            params={
                "top_k_items": 3,
                "predict_color": "true",
                "top_k_colors": 3
            },
            files={
                "query_image": (
                    image.filename,
                    image.read(),
                    image.mimetype or "image/jpeg"
                )
            },
            timeout=30
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

        rgb = color_to_rgb(color_name)

        if not items:
            return jsonify({
                "result": "No LEGO identified",
                "color": color_name,
                "rgb": rgb,
                "color_confidence": color_confidence
            })

        best = items[0]
        name = best.get("name", "Unknown")
        category = best.get("category", "Unknown")
        bin_name = choose_bin(category, name)

        result = {
            "name": name,
            "part_id": best.get("id", "Unknown"),
            "category": category,
            "confidence": round(best.get("score", 0) * 100, 1),
            "bin": bin_name,
            "color": color_name,
            "rgb": rgb,
            "color_confidence": color_confidence
        }

        print("Result:", result, flush=True)
        return jsonify(result)

    except Exception as error:
        print("Error:", error, flush=True)
        return jsonify({"error": str(error)}), 500


print("Pi 1 Brickognize server started.", flush=True)
app.run(host="0.0.0.0", port=5000)
