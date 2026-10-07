import math

from flask import Flask, abort, jsonify, make_response, redirect, request, url_for
from markupsafe import escape

app = Flask(__name__)
app.json.ensure_ascii = False   # JSON hiển thị tiếng Việt có dấu
app.json.sort_keys = False      # giữ nguyên thứ tự khoá

STUDENTS = {
    "23T1020001": {"name": "Nguyễn Nhật Tiến", "lop": "K47A",
                   "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.0}},
    "23T1020002": {"name": "Trần Quang Bình", "lop": "K47A",
                   "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0}},
    "23T1020003": {"name": "Lê Trần Tấn Tài", "lop": "K47B",
                   "scores": {"PMMNM": 9.5, "CSDL": 9.0}},
    "23T1020004": {"name": "Hoàng Đình Gia Bảo", "lop": "K47B",
                   "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0}},
    "23T1020005": {"name": "Ngô Thị Như Quỳnh", "lop": "K47A",
                   "scores": {}},
    "23T1020006": {"name": "Hồ Bảo Toàn", "lop": "K47C",
                   "scores": {"PMMNM": 7.5, "MMT": 8.0}},
}


# ---------------------------------------------------------------- Hàm phụ
def average(scores):
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


def rank(avg):
    if avg is None:
        return "Chưa có điểm"
    if avg >= 8.5:
        return "Giỏi"
    if avg >= 7.0:
        return "Khá"
    if avg >= 5.0:
        return "Trung bình"
    return "Yếu"


def student_summary(mssv):
    s = STUDENTS[mssv]
    avg = average(s["scores"])
    return {"mssv": mssv, "name": s["name"], "lop": s["lop"],
            "scores": s["scores"], "average": avg, "rank": rank(avg)}


def layout(title, body):
    """`title` được escape; `body` chèn nguyên văn (người gọi tự escape dữ liệu)."""
    return f"""<!doctype html>
<html lang="vi">
<head><meta charset="utf-8"><title>{escape(title)} - Sổ điểm</title></head>
<body>
<nav>
  <a href="{url_for('home')}">Trang chủ</a> ·
  <a href="{url_for('student_list')}">Sinh viên</a> ·
  <a href="{url_for('search')}">Tìm kiếm sinh viên</a>
</nav>
<hr>
{body}
</body>
</html>"""


def fmt_avg(avg):
    return "—" if avg is None else f"{avg:.2f}"


def parse_float(raw):
    """Trả về float hữu hạn, hoặc None nếu raw không hợp lệ."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


# ------------------------------------------------------------ Giao diện web
@app.route("/")
def home():
    classes = {s["lop"] for s in STUDENTS.values()}
    body = f"""<h1>Sổ điểm lớp học</h1>
<p>Tổng số sinh viên: {len(STUDENTS)}</p>
<p>Số lớp: {len(classes)}</p>
<ul>
  <li><a href="{url_for('student_list')}">Danh sách sinh viên</a></li>
  <li><a href="{url_for('api_students')}">API JSON danh sách sinh viên</a></li>
</ul>"""
    return layout("Trang chủ", body)


@app.route("/students")
def student_list():
    lop = request.args.get("lop", "").strip()
    classes = sorted({s["lop"] for s in STUDENTS.values()})

    links = [f'<a href="{url_for("student_list")}">Tất cả</a>']
    for c in classes:
        links.append(f'<a href="{url_for("student_list", lop=c)}">{escape(c)}</a>')
    filter_bar = "<p>" + " | ".join(links) + "</p>"

    rows = []
    for mssv in STUDENTS:
        info = student_summary(mssv)
        if lop and info["lop"].lower() != lop.lower():
            continue
        rows.append(
            "<tr>"
            f'<td><a href="{url_for("student_detail", mssv=mssv)}">{escape(mssv)}</a></td>'
            f'<td>{escape(info["name"])}</td>'
            f'<td>{escape(info["lop"])}</td>'
            f'<td>{fmt_avg(info["average"])}</td>'
            f'<td>{escape(info["rank"])}</td>'
            "</tr>"
        )

    if rows:
        table = ("<table border='1' cellpadding='4'>"
                 "<tr><th>MSSV</th><th>Họ tên</th><th>Lớp</th>"
                 "<th>Điểm TB</th><th>Xếp loại</th></tr>"
                 + "".join(rows) + "</table>")
    else:
        table = "<p>Không có sinh viên phù hợp.</p>"
    return layout("Danh sách sinh viên", "<h1>Danh sách sinh viên</h1>" + filter_bar + table)


@app.route("/students/<mssv>")
def student_detail(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    info = student_summary(mssv)

    score_rows = "".join(
        f"<tr><td>{escape(course)}</td><td>{score}</td></tr>"
        for course, score in info["scores"].items()
    )
    if score_rows:
        scores_html = ("<table border='1' cellpadding='4'>"
                       "<tr><th>Học phần</th><th>Điểm</th></tr>"
                       + score_rows + "</table>")
    else:
        scores_html = "<p>Chưa có điểm.</p>"

    body = f"""<h1>{escape(info['name'])}</h1>
<p>MSSV: {escape(mssv)}</p>
<p>Lớp: <a href="{url_for('student_list', lop=info['lop'])}">{escape(info['lop'])}</a></p>
<p>Điểm TB: {fmt_avg(info['average'])} · Xếp loại: {escape(info['rank'])}</p>
{scores_html}
<p><a href="{url_for('student_export', mssv=mssv)}">Tải bảng điểm (CSV)</a></p>
<p>Link rút gọn: <a href="{url_for('short_link', mssv=mssv)}">{escape(url_for('short_link', mssv=mssv))}</a></p>"""
    return layout(info["name"], body)


@app.route("/sv/<mssv>")
def short_link(mssv):
    return redirect(url_for("student_detail", mssv=mssv), code=301)


@app.route("/students/<mssv>/export")
def student_export(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    lines = ["hoc_phan,diem"]
    lines += [f"{course},{score}" for course, score in STUDENTS[mssv]["scores"].items()]
    response = make_response("\n".join(lines) + "\n")
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=diem_{mssv}.csv"
    return response


@app.route("/search")
def search():
    q = request.args.get("q", "")
    keyword = q.strip().lower()

    form = f"""<form method="get" action="{url_for('search')}">
  <input type="text" name="q" value="{escape(q)}">
  <button type="submit">Tìm</button>
</form>"""

    result_html = ""
    if keyword:
        found = [m for m, s in STUDENTS.items()
                 if keyword in s["name"].lower() or keyword in m.lower()]
        items = "".join(
            f'<li><a href="{url_for("student_detail", mssv=m)}">{escape(m)}</a>'
            f' – {escape(STUDENTS[m]["name"])}</li>'
            for m in found
        )
        result_html = (f"<p>Tìm thấy {len(found)} kết quả cho “{escape(q)}”</p>"
                       f"<ul>{items}</ul>")
    return layout("Tìm kiếm", "<h1>Tìm kiếm sinh viên</h1>" + form + result_html)


# ----------------------------------------------------------------- API JSON
@app.route("/api/students")
def api_students():
    lop = request.args.get("lop")
    raw_min = request.args.get("min_avg")

    min_avg = None
    if raw_min is not None:                      # có tham số -> phải hợp lệ
        min_avg = parse_float(raw_min)
        if min_avg is None:
            abort(400, description="min_avg phải là một số.")

    result = []
    for mssv in STUDENTS:
        info = student_summary(mssv)
        if lop is not None and info["lop"].lower() != lop.lower():
            continue
        if min_avg is not None and (info["average"] is None or info["average"] < min_avg):
            continue
        result.append(info)
    return jsonify(result)


@app.route("/api/students/<mssv>")
def api_student(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    return jsonify(student_summary(mssv))


@app.route("/api/students/<mssv>/scores/<course>", methods=["GET", "PUT", "DELETE"])
def student_score(mssv, course):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    course = course.upper()
    scores = STUDENTS[mssv]["scores"]

    if request.method == "GET":
        if course not in scores:
            abort(404, description=f"{mssv} chưa có điểm học phần {course}.")
        return jsonify({"mssv": mssv, "course": course, "score": scores[course]})

    if request.method == "DELETE":
        if course not in scores:
            abort(404, description=f"{mssv} chưa có điểm học phần {course}.")
        del scores[course]
        return "", 204

    # PUT
    raw = request.args.get("score")
    if raw is None:
        abort(400, description="Thiếu tham số score.")
    score = parse_float(raw)
    if score is None:
        abort(400, description="score phải là một số.")
    if not 0 <= score <= 10:
        abort(400, description="score phải nằm trong khoảng [0, 10].")

    existed = course in scores
    scores[course] = score
    response = jsonify({"mssv": mssv, "course": course, "score": score,
                        "average": average(scores)})
    if existed:
        response.status_code = 200
    else:
        response.status_code = 201
        response.headers["Location"] = url_for("student_score", mssv=mssv, course=course)
    return response


# ------------------------------------------------------------------ Lỗi chung
ERROR_TITLES = {
    400: "Dữ liệu không hợp lệ",
    404: "Không tìm thấy",
    405: "Phương thức không được hỗ trợ",
}


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
def handle_error(error):
    code = error.code
    title = ERROR_TITLES[code]
    if request.path.startswith("/api/"):
        response = jsonify({"error": title, "detail": error.description})
    else:
        body = (f"<h1>{code} – {escape(title)}</h1>"
                f"<p>{escape(error.description)}</p>")
        response = make_response(layout(f"{code} {title}", body))
    response.status_code = code
    if code == 405 and getattr(error, "valid_methods", None):
        response.headers["Allow"] = ", ".join(error.valid_methods)
    return response
