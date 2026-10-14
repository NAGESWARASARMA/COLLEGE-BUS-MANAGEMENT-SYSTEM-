import cv2
import requests
import sys
import time

SERVER_URL = "http://127.0.0.1:5000/api/scan"

# Choose Arrival or Departure when starting the scanner.
event = sys.argv[1].title() if len(sys.argv) > 1 else "Arrival"

if event not in ("Arrival", "Departure"):
    print("Use: py scanner.py Arrival")
    print("Or:  py scanner.py Departure")
    raise SystemExit

camera = cv2.VideoCapture(0)
detector = cv2.QRCodeDetector()

if not camera.isOpened():
    print("Camera not found. Check your webcam connection.")
    raise SystemExit

last_scanned = {}
cooldown_seconds = 30

print("Scanner started:", event)
print("Show a bus QR code to the camera.")
print("Press Q to stop scanning.")

try:
    while True:
        success, frame = camera.read()

        if not success:
            print("Could not read the camera.")
            break

        bus_number, points, _ = detector.detectAndDecode(frame)

        if bus_number:
            bus_number = bus_number.strip().upper()
            current_time = time.time()

            if current_time - last_scanned.get(bus_number, 0) >= cooldown_seconds:
                try:
                    response = requests.post(
                        SERVER_URL,
                        json={
                            "bus_number": bus_number,
                            "event": event
                        },
                        timeout=5
                    )

                    result = response.json()
                    print(result.get("message", "Scan processed."))

                    if response.ok and result.get("success"):
                        last_scanned[bus_number] = current_time

                except requests.RequestException as error:
                    print("Cannot contact the server:", error)

            if points is not None:
                points = points.astype(int)

                for i in range(len(points[0])):
                    point1 = tuple(points[0][i])
                    point2 = tuple(points[0][(i + 1) % len(points[0])])
                    cv2.line(frame, point1, point2, (0, 255, 0), 3)

            cv2.putText(
                frame,
                "Bus: " + bus_number,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

        cv2.putText(
            frame,
            "Mode: " + event + " | Press Q to quit",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.imshow("College Bus QR Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camera.release()
    cv2.destroyAllWindows()