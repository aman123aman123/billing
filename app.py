from flask import Flask, Response
from pyzbar import pyzbar
import cv2
from flask_ngrok import run_with_ngrok
import numpy as np

app = Flask(__name__)

run_with_ngrok(app)

camera=cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        # Convert the frame to grayscale for barcode detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Find barcodes in the frame
        barcodes = pyzbar.decode(gray)

        # Process detected barcodes
        for barcode in barcodes:
            # Extract barcode data
            barcode_data = barcode.data.decode('utf-8')
            print(barcode_data)

            # Draw a rectangle around the barcode
            rect_points = barcode.polygon
            if len(rect_points) == 4:
                rect_points = [(p.x, p.y) for p in rect_points]
                rect_points = [(int(x), int(y)) for x, y in rect_points]
                cv2.polylines(frame, [np.array(rect_points)], True, (0, 255, 0), 2)

            # Display the barcode data
            cv2.putText(frame, barcode_data, (rect_points[0][0], rect_points[0][1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Encode the frame as JPEG
        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')



@app.route('/video')
def video():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')
  

if __name__ == '__main__':
    app.run(debug=True)

