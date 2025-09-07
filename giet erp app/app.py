from flask import Flask, request, render_template_string, session
import requests
from tabulate import tabulate

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Common request headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://gietuerp.in",
    "Referer": "https://gietuerp.in/StudentDashboard/DayWiseAttendance",
    "X-Requested-With": "XMLHttpRequest"
}

cookies = {
    ".AspNetCore.Antiforgery.EVmtgmueGTo": "your_antiforgery_token_here",
    "UserLoginCookie": "your_user_login_cookie_here",
    ".AspNetCore.Mvc.CookieTempDataProvider": "your_temp_data_cookie_here"
}

url = "https://gietuerp.in/AttendanceReport/GetAttendanceByRollNo"


def fetch_attendance(roll_no):
    payload = {"vintSemester": "-1", "vvchRollNo": roll_no}
    response = requests.post(url, headers=headers, cookies=cookies, data=payload)
    if response.ok:
        try:
            return response.json().get("dataAttendance", [])
        except ValueError:
            return []
    return []


@app.route("/", methods=["GET", "POST"])
def home():
    roll_no = session.get("rollno")
    if request.method == "POST":
        roll_no = request.form.get("rollno", roll_no)
        session["rollno"] = roll_no
        choice = request.form.get("choice")
        table_data = fetch_attendance(roll_no)

        if not table_data:
            return f"<h3 style='color:red;'>⚠️ No attendance data found for {roll_no}</h3><br><a href='/'>Back</a>"

        # ---------------- Daywise Table ----------------
        if choice == "daywise":
            headers_table = list(table_data[0].keys())
            rows = [list(item.values()) for item in table_data]
            table_html = tabulate(rows, headers=headers_table, tablefmt="html")
            return render_template_string("""
            <html>
            <head>
                <title>Daywise Attendance</title>
                <style>
                    body {background-color:#121212;color:#e0e0e0;font-family:Arial,sans-serif;text-align:center;margin:0;padding:20px;}
                    table {border-collapse: collapse;margin:20px auto;width:95%;background:#1e1e1e;color:#e0e0e0;border-radius:10px;overflow:hidden;}
                    th, td {border:1px solid #333;padding:10px;text-align:center;}
                    th {background:#ff6600;color:white;}
                    tr:nth-child(even){background:#2a2a2a;}
                    a, button {display:inline-block;margin-top:15px;padding:10px 15px;background:#ff6600;color:white;text-decoration:none;border-radius:5px;border:none;cursor:pointer;}
                    a:hover, button:hover{background:#ff8533;}
                </style>
            </head>
            <body>
                <div style="overflow-x:auto;">{{ table_html|safe }}</div>
                <a href="/">🔙 Back</a>
            </body>
            </html>
            """, table_html=table_html)

        # ---------------- Dashboard ----------------
        elif choice == "dashboard":
            attended_total, classes_total = 0.0, 0.0
            theory_attended, theory_total = 0.0, 0.0
            lab_attended, lab_total = 0.0, 0.0

            for row in table_data:
                for subject, value in row.items():
                    if subject == "AttendanceDate": continue
                    try:
                        attended, total = map(float, value.split("/"))
                        attended_total += attended
                        classes_total += total
                        if "lab" in subject.lower():
                            lab_attended += attended
                            lab_total += total
                        else:
                            theory_attended += attended
                            theory_total += total
                    except: 
                        pass

            # Exact percentages
            overall_perc = round(attended_total / classes_total * 100, 2) if classes_total else 0
            theory_perc = round(theory_attended / theory_total * 100, 2) if theory_total else 0
            lab_perc = round(lab_attended / lab_total * 100, 2) if lab_total else 0

            theory_color = "green" if theory_perc >= 80 else "red"
            lab_color = "green" if lab_perc >= 80 else "red"
            overall_color = "green" if overall_perc >= 80 else "red"

            return render_template_string("""
            <html>
            <head>
                <title>Attendance Dashboard</title>
                <style>
                    body {background-color:#121212;color:#e0e0e0;font-family:Arial,sans-serif;text-align:center;margin:0;padding:20px;}
                    .card{background:#1e1e1e;border-radius:15px;padding:30px;max-width:700px;margin:30px auto;box-shadow:0 0 15px rgba(0,0,0,0.6);}
                    .header{font-size:22px;margin-bottom:20px;}
                    .container{display:flex;justify-content:center;gap:40px;flex-wrap:wrap;margin-top:20px;}
                    .circle{width:120px;height:120px;border-radius:50%;display:flex;justify-content:center;align-items:center;font-size:22px;font-weight:bold;color:white;margin:0 auto 10px auto;background:conic-gradient(#333 0%,#333 100%);}
                    .label{text-align:center;font-size:16px;}
                    a, button{display:inline-block;margin-top:25px;padding:10px 15px;background:#ff6600;color:white;text-decoration:none;border-radius:5px;border:none;cursor:pointer;}
                    a:hover, button:hover{background:#ff8533;}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="header">📊 Attendance Dashboard</div>
                    <div class="container">
                        <div>
                            <div class="circle" id="theory">0%</div>
                            <div class="label">Theory</div>
                        </div>
                        <div>
                            <div class="circle" id="lab">0%</div>
                            <div class="label">Lab</div>
                        </div>
                        <div>
                            <div class="circle" id="overall">0%</div>
                            <div class="label">Total</div>
                        </div>
                    </div>
                </div>

                <script>
                function animateCircle(id, percentage, color) {
                    let circle = document.getElementById(id);
                    let current = 0;
                    let target = percentage;
                    let interval = setInterval(() => {
                        if(current >= target){
                            clearInterval(interval);
                            circle.innerText = target.toFixed(2) + "%"; // exact percentage
                        } else {
                            current++;
                            circle.innerText = current + "%";
                            circle.style.background = `conic-gradient(${color} ${current}%, #333 ${current}%)`;
                        }
                    }, 15);
                }

                animateCircle("theory", {{ theory_perc }}, "{{ theory_color }}");
                animateCircle("lab", {{ lab_perc }}, "{{ lab_color }}");
                animateCircle("overall", {{ overall_perc }}, "{{ overall_color }}");
                </script>

                <a href="/">🔙 Back</a>
            </body>
            </html>
            """, theory_perc=theory_perc, lab_perc=lab_perc, overall_perc=overall_perc,
                 theory_color=theory_color, lab_color=lab_color, overall_color=overall_color)

    # ---------------- First Load ----------------
    return render_template_string("""
    <html>
    <head>
        <title>Enter Roll Number</title>
        <style>
            body {background-color:#121212;color:#e0e0e0;font-family:Arial,sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
            .form-box{background:#1e1e1e;padding:30px;border-radius:10px;box-shadow:0 0 10px rgba(0,0,0,0.5);text-align:center;}
            input[type=text]{padding:10px;width:250px;font-size:16px;border-radius:5px;border:1px solid #444;background:#2a2a2a;color:#fff;}
            button{padding:10px 15px;margin:10px;font-size:16px;background:#ff6600;color:white;border:none;cursor:pointer;border-radius:5px;}
            button:hover{background:#ff8533;}
        </style>
    </head>
    <body>
        <div class="form-box">
            <h2>🎓 Enter Roll Number</h2>
            <form method="POST">
                <input type="text" name="rollno" placeholder="Enter Roll No" value="{{ roll_no or '' }}" required>
                <br><br>
                <button type="submit" name="choice" value="daywise">📅 Daywise</button>
                <button type="submit" name="choice" value="dashboard">% Percentages</button>
            </form>
        </div>
    </body>
    </html>
    """, roll_no=roll_no)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
