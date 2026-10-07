# Sổ điểm lớp học – Chương 3

Chạy:

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    flask --app sodiem run --debug --port 8000

## 1. flask --app sodiem routes (10 dòng)

    Endpoint        Methods           Rule
    api_student     GET               /api/students/<mssv>
    api_students    GET               /api/students
    home            GET               /
    search          GET               /search
    short_link      GET               /sv/<mssv>
    static          GET               /static/<path:filename>
    student_detail  GET               /students/<mssv>
    student_export  GET               /students/<mssv>/export
    student_list    GET               /students
    student_score   DELETE, GET, PUT  /api/students/<mssv>/scores/<course>

## 2. Kết quả curl

| Lệnh | Kết quả |
|---|---|
| `curl -i $B/sv/23T1020001` | `301 MOVED PERMANENTLY`, `Location: /students/23T1020001` |
| `curl -i $B/students/23T1020001/export` | `200 OK`, `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename=diem_23T1020001.csv`; body `hoc_phan,diem / PMMNM,8.5 / CSDL,7.0 / MMT,9.0` |
| `curl "$B/api/students?lop=k47a&min_avg=7"` | `[{"mssv":"23T1020001","name":"Nguyễn Văn An",...,"average":8.17,"rank":"Khá"}]` |
| `curl -i "$B/api/students?min_avg=abc"` | `400 BAD REQUEST`, `{"error":"Dữ liệu không hợp lệ","detail":"min_avg phải là một số."}` |
| `curl -i $B/api/students/999` | `404 NOT FOUND`, `{"error":"Không tìm thấy","detail":"Không có sinh viên với MSSV = 999."}` |
| `curl -i -X PUT "$S/web?score=9"` | `201 CREATED`, `Location: /api/students/23T1020005/scores/WEB`, `{"mssv":"23T1020005","course":"WEB","score":9.0,"average":9.0}` |
| `curl -X PUT "$S/WEB?score=7.5"` | `200 OK`, `{"mssv":"23T1020005","course":"WEB","score":7.5,"average":7.5}` |
| `curl -i -X PUT "$S/WEB?score=11"` | `400 BAD REQUEST`, `{"error":"Dữ liệu không hợp lệ","detail":"score phải nằm trong khoảng [0, 10]."}` |
| `curl -i -X PUT "$S/WEB?score=0"` | `200 OK`, `score` = 0.0 (điểm 0 hợp lệ) |
| `curl -i -X DELETE $S/WEB` | `204 NO CONTENT`, body rỗng |
| `curl -i -X POST $S/WEB` | `405 METHOD NOT ALLOWED`, JSON `{"error":"Phương thức không được hỗ trợ",...}` |
| `curl -i -X POST $B/students` | `405 METHOD NOT ALLOWED`, trang HTML dùng `layout()` |

Kiểm tra XSS: `/search?q="><script>alert(1)</script>` → từ khoá được escape ở cả hai chỗ
(`value="&#34;&gt;&lt;script&gt;..."` và dòng "Tìm thấy N kết quả"), không có hộp thoại.

## 3. Trả lời ngắn

**Vì sao Câu 4 dùng 301 còn Câu 8 trả 201 kèm Location?**
301 nghĩa là *tài nguyên đã chuyển vĩnh viễn* sang URL khác: `/sv/<mssv>` chỉ là địa chỉ
rút gọn, trình duyệt/công cụ tìm kiếm nên ghi nhớ và dùng thẳng URL mới. 201 nghĩa là
*yêu cầu thành công và đã tạo ra một tài nguyên mới*; header `Location` cho client biết
URL của tài nguyên vừa tạo (ở đây chính là URL của request), không phải bảo client đi nơi khác.

**Thêm điểm cho 23T1020005 rồi khởi động lại server, điểm đó còn không? Vì sao?**
Không còn. Dữ liệu nằm trong dict `STUDENTS` trong bộ nhớ của tiến trình Python. Khi server
khởi động lại, mã được nạp lại và `STUDENTS` trở về giá trị khai báo ban đầu. Muốn giữ lại
phải lưu vào nơi bền vững (file, SQLite/cơ sở dữ liệu).

**Vì sao dùng được `request` trong hàm xử lý lỗi dù nó không phải view function?**
`request` là một proxy gắn với *request context*. Flask đẩy context này vào đầu mỗi request
và chỉ gỡ ra sau khi xử lý xong, kể cả khi gọi error handler. Hàm xử lý lỗi chạy bên trong
cùng request đó nên `request` vẫn hợp lệ, không phụ thuộc hàm đó có phải view function hay không.
