# AI Smart Grid Optimization - Interactive Dashboard with Login (Dark Mode Graph)
# Author: Atharv Jadhav

from flask import Flask, render_template_string, request, redirect, url_for, session
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = "smartgrid_secret_key"

# ---------------- LOGIN PAGE ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"].strip()

        if username == "atharv jadhav" and password == "atharv2112":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template_string(login_html, error="Invalid username or password!")

    return render_template_string(login_html)

# ---------------- DASHBOARD PAGE ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    graph_type = request.args.get('graph', 'line')
    selected_day = int(request.args.get('day', 0))

    # --- Generate sample data ---
    np.random.seed(42)
    total_days = 8
    hours_per_day = 24
    total_hours = total_days * hours_per_day
    time_index = pd.date_range(datetime.now() - timedelta(days=total_days-1), periods=total_hours, freq='H')

    solar = np.clip(50 + 30*np.sin(np.linspace(0, 5*np.pi, total_hours)) + np.random.randn(total_hours)*5, 0, None)
    wind = np.clip(40 + 20*np.sin(np.linspace(0, 6*np.pi, total_hours)+1) + np.random.randn(total_hours)*5, 0, None)
    demand = 70 + 10*np.sin(np.linspace(0, 4*np.pi, total_hours)) + np.random.randn(total_hours)*5
    temp = np.random.uniform(20, 35, total_hours)

    df = pd.DataFrame({
        "time": time_index,
        "solar": solar,
        "wind": wind,
        "demand": demand,
        "temp": temp
    })

    df["actual_supply"] = df["solar"] + df["wind"]

    # --- Battery Simulation ---
    battery_capacity, battery_charge, efficiency = 100, 50, 0.9
    battery_levels = []
    for i in range(len(df)):
        diff = df["actual_supply"][i] - df["demand"][i]
        if diff > 0:
            battery_charge += min(diff * efficiency, battery_capacity - battery_charge)
        else:
            battery_charge -= min(abs(diff) / efficiency, battery_charge)
        battery_levels.append(battery_charge)
    df["battery_level"] = battery_levels

    # --- Stability Check ---
    df["grid_stability"] = df.apply(
        lambda x: "Stable" if abs(x["actual_supply"] - x["demand"]) < 10 else "Unstable",
        axis=1
    )

    df["date"] = df["time"].dt.strftime("%Y-%m-%d")
    df["time_only"] = df["time"].dt.strftime("%I:%M %p")

    unique_days = sorted(df["date"].unique())
    selected_date = unique_days[selected_day] if selected_day < len(unique_days) else unique_days[-1]
    day_df = df[df["date"] == selected_date]

    # --- Dark Graph ---
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_facecolor("#1e272e")

    if graph_type == "bar":
        x = np.arange(len(day_df))
        ax.bar(x - 0.3, day_df["solar"], width=0.2, label="Solar", color="#fbc531")
        ax.bar(x - 0.1, day_df["wind"], width=0.2, label="Wind", color="#00a8ff")
        ax.bar(x + 0.3, day_df["demand"], width=0.2, label="Demand", color="#e84118")
        ax.bar(x + 0.1, day_df["battery_level"], width=0.2, label="Battery", color="#e1b12c")
        plt.xticks(x[::3], day_df["time_only"].iloc[::3], rotation=45, color="white")
    elif graph_type == "scatter":
        ax.scatter(day_df["time_only"], day_df["solar"], label="Solar", c="#fbc531")
        ax.scatter(day_df["time_only"], day_df["wind"], label="Wind", c="#00a8ff")
        ax.scatter(day_df["time_only"], day_df["demand"], label="Demand", c="#e84118")
        ax.scatter(day_df["time_only"], day_df["battery_level"], label="Battery", c="#e1b12c")
    else:
        ax.plot(day_df["time_only"], day_df["solar"], label="Solar", color="#fbc531", linewidth=2)
        ax.plot(day_df["time_only"], day_df["wind"], label="Wind", color="#00a8ff", linewidth=2)
        ax.plot(day_df["time_only"], day_df["demand"], label="Demand", color="#e84118", linestyle="--", linewidth=2)
        ax.plot(day_df["time_only"], day_df["battery_level"], label="Battery", color="#e1b12c", linewidth=2)

    ax.set_title(f"⚡ AI Smart Grid - {selected_date} ({graph_type.capitalize()} Plot)", color="white", fontsize=14)
    ax.set_xlabel("Time", color="white")
    ax.set_ylabel("Power (%)", color="white")
    ax.legend(facecolor="#2f3640", edgecolor="white", labelcolor="white")
    ax.grid(True, color="#485460")

    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", facecolor="#1e272e")
    buf.seek(0)
    graph_url = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    # --- Render Dashboard ---
    return render_template_string(
        dashboard_html,
        graph_url=graph_url,
        unique_days=list(enumerate(unique_days)),  # ✅ pass enumerate safely
        selected_day=selected_day,
        selected_date=selected_date,
        graph_type=graph_type,
        day_df=day_df
    )

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- HTML Templates ----------------
login_html = """
<!DOCTYPE html>
<html>
<head>
<title>Login - Smart Grid Dashboard</title>
<style>
body {
    background-color: #1e272e;
    color: white;
    font-family: Arial;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}
.login-box {
    background: #2f3640;
    padding: 30px;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 0 10px #718093;
}
input {
    width: 90%;
    padding: 10px;
    margin: 8px 0;
    border: none;
    border-radius: 6px;
    background: #353b48;
    color: white;
}
button {
    background-color: #00a8ff;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}
button:hover { background-color: #0097e6; }
.error { color: #e84118; }
</style>
</head>
<body>
    <div class="login-box">
        <h2>🔒 Login to Smart Grid Dashboard</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Login</button>
        </form>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
    </div>
</body>
</html>
"""

dashboard_html = """
<html>
<head>
    <title>AI Smart Grid Dashboard</title>
    <style>
        body {
            font-family: Arial;
            background: #1e272e;
            color: white;
            margin: 0;
            padding: 20px;
        }
        h1 { color: #00a8ff; text-align: center; }
        .container {
            width: 95%;
            margin: auto;
            background: #2f3640;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 0 10px #718093;
        }
        a.logout {
            float: right;
            background: #e84118;
            color: white;
            padding: 8px 15px;
            border-radius: 6px;
            text-decoration: none;
        }
        select, button {
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #718093;
            margin: 5px;
            font-size: 15px;
            background-color: #353b48;
            color: white;
        }
        button { background-color: #00a8ff; cursor: pointer; }
        button:hover { background-color: #0097e6; }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #718093;
            padding: 8px;
            text-align: center;
        }
        th { background-color: #273c75; }
        .stable-cell { background-color: #44bd32; color: white; font-weight: bold; }
        .unstable-cell { background-color: #e84118; color: white; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <a class="logout" href="/logout">Logout</a>
        <h1>⚡ AI Smart Grid Optimization Dashboard</h1>
        <form method="get" action="/dashboard">
            <label for="day">Select Day:</label>
            <select name="day" id="day">
                {% for i, d in unique_days %}
                    <option value="{{i}}" {% if i == selected_day %}selected{% endif %}>{{d}}</option>
                {% endfor %}
            </select>
            <label for="graph">Graph Type:</label>
            <select name="graph" id="graph">
                <option value="line" {% if graph_type=='line' %}selected{% endif %}>Line Plot</option>
                <option value="bar" {% if graph_type=='bar' %}selected{% endif %}>Bar Plot</option>
                <option value="scatter" {% if graph_type=='scatter' %}selected{% endif %}>Matplot (Scatter)</option>
            </select>
            <button type="submit">View Data</button>
        </form>

        <img src="data:image/png;base64,{{graph_url}}" width="100%" />

        <h2 style="text-align:center;">Grid Data - {{selected_date}}</h2>
        <table>
            <tr>
                <th>Time</th>
                <th>Solar (%)</th>
                <th>Wind (%)</th>
                <th>Actual Supply (%)</th>
                <th>Demand (%)</th>
                <th>Battery (%)</th>
                <th>Stability</th>
            </tr>
            {% for _, row in day_df.iterrows() %}
            <tr>
                <td>{{row.time_only}}</td>
                <td>{{"%.2f"|format(row.solar)}}%</td>
                <td>{{"%.2f"|format(row.wind)}}%</td>
                <td>{{"%.2f"|format(row.actual_supply)}}%</td>
                <td>{{"%.2f"|format(row.demand)}}%</td>
                <td>{{"%.2f"|format(row.battery_level)}}%</td>
                <td class="{{'stable-cell' if row.grid_stability=='Stable' else 'unstable-cell'}}">{{row.grid_stability}}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)

