from flask import Flask, request, jsonify, render_template_string
from utils import process_data, get_positions

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>ESP Position Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background: #f5f5f5;
        }
        h1 {
            margin-top: 20px;
        }
        #canvas {
            background: white;
            border: 2px solid black;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>Live Device Position Map</h1>
    <canvas id="canvas" width="800" height="600"></canvas>

    <script>
        const canvas = document.getElementById("canvas");
        const ctx = canvas.getContext("2d");

        const scale = 20;   // 1 meter = 20 pixels
        const offsetX = 100;
        const offsetY = 500;

        function drawAxes() {
            ctx.strokeStyle = "black";
            ctx.lineWidth = 1;

            // X-axis
            ctx.beginPath();
            ctx.moveTo(50, offsetY);
            ctx.lineTo(750, offsetY);
            ctx.stroke();

            // Y-axis
            ctx.beginPath();
            ctx.moveTo(offsetX, 50);
            ctx.lineTo(offsetX, 550);
            ctx.stroke();

            ctx.fillStyle = "black";
            ctx.fillText("X", 760, offsetY + 5);
            ctx.fillText("Y", offsetX - 10, 40);
        }

        function drawPoints(data) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            drawAxes();

            for (const mac in data) {
                const pos = data[mac];
                const x = pos[0];
                const y = pos[1];

                const px = offsetX + x * scale;
                const py = offsetY - y * scale;

                ctx.beginPath();
                ctx.arc(px, py, 6, 0, 2 * Math.PI);
                ctx.fillStyle = "red";
                ctx.fill();

                ctx.fillStyle = "black";
                ctx.fillText(mac, px + 10, py - 10);
                ctx.fillText(`(${x.toFixed(2)}, ${y.toFixed(2)})`, px + 10, py + 10);
            }
        }

        async function updatePositions() {
            try {
                const response = await fetch("/positions");
                const data = await response.json();
                drawPoints(data);
            } catch (err) {
                console.error("Error fetching positions:", err);
            }
        }

        setInterval(updatePositions, 1000);
        updatePositions();
    </script>
</body>
</html>
"""

@app.route('/endpoint', methods=['POST'])
def receive_data():
    data = request.json
    print("Received:", data)
    process_data(data)
    return jsonify({"status": "ok"})

@app.route('/positions', methods=['GET'])
def positions():
    return jsonify(get_positions())

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)