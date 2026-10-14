from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "college-bus-management-key"

DATABASE = "college_buses.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bus_management (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_type TEXT,
            bus_number TEXT,
            registration_number TEXT,
            driver_name TEXT,
            driver_phone TEXT,
            route TEXT,
            starting_place TEXT,
            stops TEXT,
            scheduled_arrival TEXT,
            scheduled_departure TEXT,
            capacity INTEGER,
            event TEXT,
            event_time TEXT
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_db()

    buses = conn.execute("""
        SELECT * FROM bus_management
        WHERE record_type = 'BUS'
        ORDER BY id DESC
    """).fetchall()

    history = conn.execute("""
        SELECT * FROM bus_management
        WHERE record_type = 'SCAN'
        ORDER BY id DESC
        LIMIT 100
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        buses=buses,
        history=history
    )


@app.route("/add_bus", methods=["POST"])
def add_bus():
    data = request.form

    bus_number = data.get("bus_number", "").strip()
    driver_name = data.get("driver_name", "").strip()
    route = data.get("route", "").strip()

    if not bus_number or not driver_name or not route:
        flash("Bus number, driver name and route are required.", "error")
        return redirect(url_for("home"))

    try:
        capacity = int(data.get("capacity") or 0)
        if capacity < 0:
            raise ValueError
    except ValueError:
        flash("Please enter a valid bus capacity.", "error")
        return redirect(url_for("home"))

    conn = get_db()

    duplicate = conn.execute("""
        SELECT id FROM bus_management
        WHERE record_type = 'BUS' AND bus_number = ?
    """, (bus_number,)).fetchone()

    if duplicate:
        conn.close()
        flash("This bus number is already registered.", "error")
        return redirect(url_for("home"))

    conn.execute("""
        INSERT INTO bus_management (
            record_type, bus_number, registration_number,
            driver_name, driver_phone, route, starting_place,
            stops, scheduled_arrival, scheduled_departure,
            capacity, event, event_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "BUS",
        bus_number,
        data.get("registration_number", "").strip(),
        driver_name,
        data.get("driver_phone", "").strip(),
        route,
        data.get("starting_place", "").strip(),
        data.get("stops", "").strip(),
        data.get("scheduled_arrival", "").strip(),
        data.get("scheduled_departure", "").strip(),
        capacity,
        "",
        ""
    ))

    conn.commit()
    conn.close()

    flash("Bus registered successfully.", "success")
    return redirect(url_for("home"))


@app.route("/edit_bus/<int:bus_id>", methods=["GET", "POST"])
def edit_bus(bus_id):
    conn = get_db()

    bus = conn.execute("""
        SELECT * FROM bus_management
        WHERE id = ? AND record_type = 'BUS'
    """, (bus_id,)).fetchone()

    if bus is None:
        conn.close()
        flash("Bus record not found.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        data = request.form

        bus_number = data.get("bus_number", "").strip()
        driver_name = data.get("driver_name", "").strip()
        route = data.get("route", "").strip()

        if not bus_number or not driver_name or not route:
            flash("Bus number, driver name and route are required.", "error")
            conn.close()
            return redirect(url_for("edit_bus", bus_id=bus_id))

        try:
            capacity = int(data.get("capacity") or 0)
            if capacity < 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid bus capacity.", "error")
            conn.close()
            return redirect(url_for("edit_bus", bus_id=bus_id))

        duplicate = conn.execute("""
            SELECT id FROM bus_management
            WHERE record_type = 'BUS'
              AND bus_number = ?
              AND id != ?
        """, (bus_number, bus_id)).fetchone()

        if duplicate:
            flash("Another bus already uses this bus number.", "error")
            conn.close()
            return redirect(url_for("edit_bus", bus_id=bus_id))

        conn.execute("""
            UPDATE bus_management
            SET bus_number = ?,
                registration_number = ?,
                driver_name = ?,
                driver_phone = ?,
                route = ?,
                starting_place = ?,
                stops = ?,
                scheduled_arrival = ?,
                scheduled_departure = ?,
                capacity = ?
            WHERE id = ? AND record_type = 'BUS'
        """, (
            bus_number,
            data.get("registration_number", "").strip(),
            driver_name,
            data.get("driver_phone", "").strip(),
            route,
            data.get("starting_place", "").strip(),
            data.get("stops", "").strip(),
            data.get("scheduled_arrival", "").strip(),
            data.get("scheduled_departure", "").strip(),
            capacity,
            bus_id
        ))

        conn.commit()
        conn.close()

        flash("Bus details updated successfully.", "success")
        return redirect(url_for("home"))

    conn.close()
    return render_template("edit_bus.html", bus=bus)


@app.route("/api/scan", methods=["POST"])
def scan_bus():
    data = request.get_json(silent=True) or {}

    bus_number = str(data.get("bus_number", "")).strip()
    event = str(data.get("event", "Arrival")).strip().title()

    if not bus_number:
        return jsonify({"success": False, "message": "Bus number is required."}), 400

    if event not in ("Arrival", "Departure"):
        return jsonify({"success": False, "message": "Invalid event."}), 400

    conn = get_db()

    bus = conn.execute("""
        SELECT * FROM bus_management
        WHERE record_type = 'BUS' AND bus_number = ?
    """, (bus_number,)).fetchone()

    if bus is None:
        conn.close()
        return jsonify({
            "success": False,
            "message": "Bus is not registered."
        }), 404

    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        INSERT INTO bus_management (
            record_type, bus_number, registration_number,
            driver_name, driver_phone, route, starting_place,
            stops, scheduled_arrival, scheduled_departure,
            capacity, event, event_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "SCAN",
        bus["bus_number"],
        bus["registration_number"],
        bus["driver_name"],
        bus["driver_phone"],
        bus["route"],
        bus["starting_place"],
        bus["stops"],
        bus["scheduled_arrival"],
        bus["scheduled_departure"],
        bus["capacity"],
        event,
        scan_time
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"{bus_number}: {event} recorded successfully.",
        "bus_number": bus_number,
        "event": event,
        "event_time": scan_time
    })


if __name__ == "__main__":
    initialize_database()
    app.run(host="127.0.0.1", port=5000, debug=False)