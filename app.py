from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pid = request.form["pid"]
        arrival_time = int(request.form["arrival_time"])
        burst_time = int(request.form["burst_time"])
        priority = request.form["priority"]
        priority = int(priority) if priority else None

        conn = get_db_connection()
        conn.execute("INSERT INTO processes (pid, arrival_time, burst_time, priority) VALUES (?, ?, ?, ?)",
                     (pid, arrival_time, burst_time, priority))
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    conn = get_db_connection()
    processes = conn.execute("SELECT * FROM processes").fetchall()
    conn.close()
    return render_template("main.html", processes=processes)


@app.route("/clear", methods=["POST"])
def clear():
    conn = get_db_connection()
    conn.execute("DELETE FROM processes")
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/schedule/<algorithm>", methods=["GET"])
def schedule(algorithm):
    conn = get_db_connection()
    processes = conn.execute("SELECT * FROM processes").fetchall()
    conn.close()

    process_list = [
        {
            "id": process["id"],
            "pid": process["pid"],
            "arrival_time": process["arrival_time"],
            "burst_time": process["burst_time"],
            "priority": process["priority"]
        }
        for process in processes
    ]

    if algorithm == "fcfs":
        result = fcfs(process_list)
    elif algorithm == "sjf":
        result = sjf(process_list)
    elif algorithm == "priority":
        result = priority_scheduling(process_list)
    elif algorithm == "round_robin":
        time_quantum = int(request.args.get("time_quantum", 1))
        result = round_robin(process_list, time_quantum)
    else:
        return jsonify({"error": "Invalid algorithm"}), 400

    return jsonify(result)


def fcfs(processes):
    processes.sort(key=lambda x: x["arrival_time"])
    current_time = 0
    for process in processes:
        if current_time < process["arrival_time"]:
            current_time = process["arrival_time"]
        process["completion_time"] = current_time + process["burst_time"]
        process["turnaround_time"] = process["completion_time"] - process["arrival_time"]
        process["waiting_time"] = process["turnaround_time"] - process["burst_time"]
        current_time = process["completion_time"]
    return processes


def sjf(processes):
    processes.sort(key=lambda x: x["arrival_time"])
    completed = []
    current_time = 0
    while processes:
        available = [p for p in processes if p["arrival_time"] <= current_time]
        if not available:
            current_time += 1
            continue

        available.sort(key=lambda x: x["burst_time"])
        process = available[0]
        processes.remove(process)

        if current_time < process["arrival_time"]:
            current_time = process["arrival_time"]

        process["completion_time"] = current_time + process["burst_time"]
        process["turnaround_time"] = process["completion_time"] - process["arrival_time"]
        process["waiting_time"] = process["turnaround_time"] - process["burst_time"]
        completed.append(process)
        current_time = process["completion_time"]
    return completed


def priority_scheduling(processes):
    processes.sort(key=lambda x: x["arrival_time"])
    completed = []
    current_time = 0
    while processes:
        available = [p for p in processes if p["arrival_time"] <= current_time]
        if not available:
            current_time += 1
            continue

        available.sort(key=lambda x: (x["priority"], x["arrival_time"]))
        process = available[0]
        processes.remove(process)

        if current_time < process["arrival_time"]:
            current_time = process["arrival_time"]

        process["completion_time"] = current_time + process["burst_time"]
        process["turnaround_time"] = process["completion_time"] - process["arrival_time"]
        process["waiting_time"] = process["turnaround_time"] - process["burst_time"]
        completed.append(process)
        current_time = process["completion_time"]
    return completed


def round_robin(processes, time_quantum):
    queue = sorted(processes, key=lambda x: x["arrival_time"])
    completed = []
    current_time = 0
    while queue:
        process = queue.pop(0)

        if current_time < process["arrival_time"]:
            current_time = process["arrival_time"]

        execution_time = min(process["burst_time"], time_quantum)
        process["burst_time"] -= execution_time
        current_time += execution_time

        if process["burst_time"] == 0:
            process["completion_time"] = current_time
            process["turnaround_time"] = process["completion_time"] - process["arrival_time"]
            process["waiting_time"] = process["turnaround_time"] - (process["turnaround_time"] - execution_time)
            completed.append(process)
        else:
            queue.append(process)
    return completed


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pid TEXT NOT NULL,
            arrival_time INTEGER NOT NULL,
            burst_time INTEGER NOT NULL,
            priority INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)