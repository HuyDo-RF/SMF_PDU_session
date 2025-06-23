# Tổng quan dự án
- Mô phỏng chức năng của Session Management Function (SMF) trong mạng lõi 5G
- Mô phỏng xử lý nghiệp vụ PDU Session Establishment (tối giản) theo chuẩn 3GPP
# Yêu cầu
- Python 3.8 hoặc cao hơn
- OpenSSL
- MongoDB >= 4.x 
# Sơ đồ khối của luồng nghiệp vụ
![AMF](https://github.com/user-attachments/assets/70c67df6-d1ae-48a5-a802-b6d7ef13997a)
# Cấu trúc dự án
├── src/  
│   ├── amf/              # Cài đặt sever AMF   
│   ├── smf/              # Cài đặt sever SMF   
│   ├── udm/              # Cài đặt sever UDM  
│   ├── upf/              # Cài đặt sever UPF  
│   └── common/           # HTTP/2, PFCP, models, và worker pool 
              └── HTTP/2
              └── PFCP
              └── models
              └── worker pool
├── requirements.txt        
├── main.py                
└── test.py               # Kiểm thử dự án  
## 1. Khởi động ứng dụng (main.py)
- Cấu hình tham số: Đọc các tham số host, port, file chứng chỉ SSL/TLS và URI MongoDB từ dòng lệnh.
- Tạo và chạy song song bốn server: UPF, UDM, SMF, AMF bằng *asyncio.create_task* và *asyncio.gather* để mỗi NF hoạt động độc lập trong cùng một tiến trình bất đồng bộ.
## 2. HTTP/2 Server (common/http2.py)
- Thiết lập TLS/ALPN: Sử dụng *ssl.create_default_context* và *set_alpn_protocols* để kích hoạt HTTP/2 qua TLS.
- Xử lý events: Trong vòng lặp, đọc data, chuyển sang HTTP/2 events (RequestReceived, DataReceived, StreamEnded) và gom các frame theo stream id cho tới khi stream kết thúc thì gọi *request_handler* do từng NF cung cấp.
## 3. Worker Pool (common/worker_pool.py)
- Khởi tạo pool: Tạo num_workers task song song cùng một asyncio.queue.
- Dispatcher: Khi SMF nhận Create Session Request, nó đẩy task vào queue thay vì xử lý ngay.
- Xử lý task: Mỗi worker liên tục lấy task, chạy hàm nghiệp vụ (ví dụ process_create_session), bắt và in lỗi nếu có, rồi queue.task_done().
## 4. Data Models (common/models.py)
- Định nghĩa các message: Sử dụng Pydantic BaseModel để loại bỏ lỗi kiểu, bao gồm CreateSessionRequest, N1N2MessageTransfer, PFCPSessionEstablishmentRequest…
## 5. PFCP Protocol (common/pfcp.py)
- UDP server: Dùng socket UDP không blocking, bind cổng PFCP N4 để nhận bản tin từ SMF.
- Parse header: Đọc version, message type, SEID tối giản để phục vụ Session Establishment Request/Response.
- Xử lý và trả lời: Khi nhận request type 50, gọi handler của UPF, sau đó dựng response type 51 với SEID, IP và gửi lại.
## 6. UDM Server (udm/server.py)
- HTTP/2 handler: Tương tự HTTP/2 Server chung, định tuyến GET /nudm-sdm/v2/{imsi}.
- Xác thực IMSI: Dùng MongoDB để tìm document subscriber, trả về JSON {"status":"verified",subscriptionData} hoặc lỗi nếu không tồn tại.
## 7. UPF Server (upf/server.py)
PFCP handler: Khi nhận Session Establishment Request qua UDP, UPF tạo mới hoặc lấy SEID, cấp IP tĩnh, lưu trong sessions dict và trả về PFCP Response.
## 8. SMF Server (smf/server.py)
- HTTP/2 handler: Định tuyến POST /nsmf-pdusession/v1/sm-contexts thành handle_request.
- Submit task: Đọc JSON, parse thành CreateSessionRequest, đẩy vào WorkerPool để xử lý bất đồng bộ.
## 9. AMF Server (amf/server.py)
- HTTP/2 handler: Định tuyến POST /namf-comm/v1/ue-context/{imsi}/n1-n2-messages.
- In log chuyển bản tin: Parse JSON thành N1N2MessageTransfer và in ra console, trả về {"status":"received"}
