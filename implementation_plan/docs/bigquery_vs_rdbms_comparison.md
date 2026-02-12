# So sánh Google BigQuery và Relational Database (RDBMS)

Tài liệu này giải thích sự khác biệt giữa BigQuery và các Database quan hệ truyền thống (như MySQL, PostgreSQL) trong ngữ cảnh dự án crawl dữ liệu việc làm của bạn, đặc biệt khi kết hợp với **Google Cloud Storage (GCS) làm Data Lake**.

## 1. Bản chất kiến trúc

| Đặc điểm | Relational Database (MySQL, PostgreSQL) | Google BigQuery |
| :--- | :--- | :--- |
| **Loại hình** | **OLTP** (Online Transaction Processing) | **OLAP** (Online Analytical Processing) |
| **Tối ưu cho** | Giao dịch nhanh, cập nhật dòng lẻ tẻ (INSERT, UPDATE, DELETE từng dòng). | Phân tích dữ liệu lớn, query tổng hợp (SUM, AVG, COUNT) trên hàng triệu/tỷ dòng. |
| **Lưu trữ** | Theo dòng (Row-oriented). Đọc 1 dòng lấy hết các cột rất nhanh. | Theo cột (Columnar). Chỉ đọc các cột cần thiết trong câu query, cực nhanh cho analytics. |
| **Hạ tầng** | Cần quản lý Server (hoặc dùng Cloud SQL). Cần sizing (RAM, CPU, Disk). | **Serverless**. Không cần quản lý hạ tầng. Tự động scale theo độ lớn query. |

## 2. Tại sao BigQuery phù hợp với Data Lake (GCS)?

Bạn đang có ý định push dữ liệu lên **GCS (Data Lake)**. Đây là mô hình **ELT** (Extract - Load - Transform) hiện đại.

### a. Khả năng tích hợp với GCS (External Tables)
- **RDBMS**: Quy trình thường là Crawl -> Lưu file -> Viết script đọc file -> Insert vào DB. Nếu file lớn phải chia nhỏ (batching).
- **BigQuery**: Có thể **query trực tiếp** vào file (CSV, JSON, Parquet) nằm trên GCS mà **không cần load dữ liệu vào**. Hoặc load từ GCS vào BigQuery cực nhanh và miễn phí (batch load).

### b. Xử lý dữ liệu bán cấu trúc (Semi-structured Data)
Dữ liệu **VietnamWorks** của bạn là JSON có cấu trúc lồng nhau (Nested JSON), ví dụ: một Job có danh sách `skills`, danh sách `locations`.

- **RDBMS**:
    - Phải chuẩn hóa (Normalize) thành nhiều bảng: `Jobs`, `JobSkills`, `JobLocations`. Query phải `JOIN` nhiều bảng.
    - Hoặc dùng kiểu dữ liệu JSON (như Postgres JSONB), nhưng hiệu năng query sâu bên trong JSON không bằng BigQuery.
- **BigQuery**:
    - Hỗ trợ kiểu dữ liệu **`RECORD` (STRUCT)** và **`REPEATED` (ARRAY)**.
    - Bạn có thể lưu nguyên cấu trúc JSON của VietnamWorks vào 1 bảng duy nhất.
    - Query trực tiếp mảng `skills` bên trong bảng `jobs` mà không cần JOIN, hiệu năng rất cao.

*Ví dụ cấu trúc BigQuery cho VietnamWorks:*
```sql
SELECT
  title,
  skill
FROM `project.dataset.vietnamworks_jobs`,
UNNEST(skills) as skill -- Tự động "duỗi" mảng skills ra để đếm
WHERE list_contains(locations, 'Hà Nội')
```

## 3. Chi phí và Quản lý

- **RDBMS**:
    - Trả tiền thuê server theo giờ/tháng (ví dụ Cloud SQL) bất kể có dùng hay không.
    - Phải lo lắng về index, vacuum, partition khi dữ liệu lớn dần.
- **BigQuery**:
    - Trả tiền theo **lượng dữ liệu quét (scan)** khi query và **lượng dữ liệu lưu trữ**.
    - **Lưu trữ rất rẻ** (đặc biệt là long-term storage).
    - Không tốn tiền duy trì server khi không chạy query (Idle cost = 0 cho compute).
    - Với dữ liệu crawl (thường là append-only, ít update sửa xóa từng dòng), BigQuery cực kỳ tối ưu chi phí.

## 4. Tổng kết: Khi nào nên dùng cái nào?

### Chọn Relational Database (MySQL/Postgres) khi:
- Ứng dụng của bạn là backend cho website (User login, User profile, lưu trạng thái ứng tuyển).
- Cần phản hồi query tức thì (độ trễ milisecond).
- Dữ liệu thay đổi liên tục (update trạng thái job liên tục từng giây).

### Chọn BigQuery khi:
- **(Trường hợp của bạn)**: Tập trung vào **Data Analytics**, Data Science. Muốn tìm insight từ dữ liệu crawl (Xu hướng lương, Kỹ năng hot).
- Dữ liệu crawl về chủ yếu là để đọc và phân tích, ít khi sửa lại data cũ.
- Dùng Data Lake (GCS) làm nơi lưu trữ gốc.
- Dữ liệu có cấu trúc phức tạp (Nested JSON) và bạn lười tách bảng (JOIN).

### Lời khuyên
Với kiến trúc bạn đề xuất: **Push to GCS Data Lake -> BigQuery**, đây là chuẩn mực của **Modern Data Stack**. Nó giúp bạn linh hoạt, giảm công sức quản lý server DB và tận dụng sức mạnh xử lý dữ liệu lớn của Google.
