4. CÔNG NGHỆ SỬ DỤNG

4.1. Backend

Phần backend của hệ thống được xây dựng bằng ngôn ngữ Python, sử dụng FastAPI làm web framework chính. FastAPI là một framework hiện đại, hiệu năng cao, hỗ trợ lập trình bất đồng bộ (asynchronous) và tự động sinh tài liệu API (Swagger UI), giúp việc phát triển và kiểm thử các endpoint diễn ra nhanh chóng. Do FastAPI chỉ định nghĩa logic xử lý chứ không tự vận hành được, hệ thống cần đến Uvicorn đóng vai trò ASGI server để khởi chạy ứng dụng và xử lý đồng thời nhiều yêu cầu từ người dùng.

Về phần cơ sở dữ liệu, hệ thống sử dụng SQLAlchemy làm bộ công cụ ORM (Object-Relational Mapping), cho phép thao tác với cơ sở dữ liệu MySQL thông qua các đối tượng và cú pháp Python thay vì viết trực tiếp câu lệnh SQL, giúp mã nguồn dễ đọc và dễ bảo trì hơn. Để SQLAlchemy có thể kết nối được tới MySQL, hệ thống cần thêm thư viện driver PyMySQL làm cầu nối giao tiếp giữa Python và hệ quản trị cơ sở dữ liệu.

Việc kiểm tra và chuẩn hóa dữ liệu được đảm nhiệm bởi Pydantic và Pydantic Settings. Pydantic giúp định nghĩa cấu trúc dữ liệu đầu vào và đầu ra của từng API, tự động kiểm tra kiểu dữ liệu, các trường bắt buộc và báo lỗi rõ ràng nếu dữ liệu không hợp lệ; Pydantic Settings được dùng riêng để đọc và quản lý các biến cấu hình môi trường của hệ thống (thông tin kết nối cơ sở dữ liệu, khóa bí mật, cấu hình email...). Đi kèm với đó, thư viện email-validator hỗ trợ kiểm tra định dạng email người dùng nhập vào có hợp lệ hay không ngay tại tầng validate dữ liệu, còn python-multipart giúp FastAPI đọc được dữ liệu dạng multipart/form-data - đây là định dạng bắt buộc phải có khi người dùng tải file CV lên hệ thống.

Đối với chức năng phân tích CV, hệ thống dùng hai thư viện pypdf và python-docx để đọc và trích xuất nội dung văn bản từ file CV định dạng PDF và Word, phục vụ cho việc gửi nội dung này sang mô hình AI để phân tích.

Về bảo mật, hệ thống sử dụng cơ chế xác thực bằng JWT (JSON Web Token) thông qua thư viện python-jose để tạo và xác thực token, giúp duy trì trạng thái đăng nhập của người dùng mà không cần lưu session ở phía server. Mật khẩu người dùng trước khi lưu vào cơ sở dữ liệu được băm bằng thuật toán bcrypt thông qua thư viện passlib, đảm bảo mật khẩu gốc không bao giờ được lưu trữ hay truyền đi dưới dạng văn bản thuần.

Cuối cùng, để đảm bảo chất lượng và tính đúng đắn của hệ thống trong suốt quá trình phát triển, các chức năng đều được viết kiểm thử tự động bằng Pytest - công cụ kiểm thử phổ biến của Python, cho phép chạy lại toàn bộ các kịch bản kiểm tra chỉ bằng một lệnh duy nhất mỗi khi có thay đổi mã nguồn.

4.2. Frontend

Khác với các hệ thống thường tách frontend thành một dự án riêng biệt sử dụng các framework như React hay Vue, giao diện người dùng của hệ thống này được xây dựng theo hướng tối giản: toàn bộ giao diện nằm gọn trong một file HTML duy nhất, sử dụng JavaScript thuần (không qua framework hay thư viện quản lý state nào) để gọi trực tiếp đến các API của backend thông qua hàm fetch có sẵn của trình duyệt. Cách tiếp cận này giúp việc triển khai đơn giản, không cần bước biên dịch (build), phù hợp với quy mô của một hệ thống quản lý tuyển dụng nội bộ.

Về giao diện, hệ thống sử dụng Tailwind CSS - một framework CSS theo hướng tiện ích (utility-first), cho phép xây dựng giao diện nhanh chóng bằng cách ghép các lớp (class) có sẵn ngay trong HTML mà không cần viết file CSS riêng, đồng thời đảm bảo giao diện hiển thị tốt trên nhiều kích thước màn hình khác nhau. Các biểu đồ thống kê trên trang Dashboard (biểu đồ cột, biểu đồ tròn, biểu đồ đường) được vẽ bằng thư viện Chart.js dựa trên dữ liệu lấy về từ API. Font Awesome được dùng để cung cấp các icon trực quan cho nút bấm và thanh menu, còn font chữ Inter lấy từ Google Fonts giúp giao diện trông hiện đại, tối giản và dễ đọc hơn.

4.3. Tích hợp ngoài

Hệ thống có tích hợp với hai dịch vụ bên ngoài. Thứ nhất là dịch vụ gửi email tự động thông qua Gmail SMTP (smtp.gmail.com, cổng 587) - mỗi khi có sự kiện cần thông báo cho ứng viên như xác nhận nộp hồ sơ, mời phỏng vấn, gửi thư mời nhận việc hay cấp lại mật khẩu, hệ thống sẽ tự động soạn và gửi email qua máy chủ SMTP của Google.

Thứ hai là tích hợp với dịch vụ AI của Google thông qua Google AI Studio, sử dụng mô hình Gemini (gemini-3.6-flash) để phân tích nội dung CV của ứng viên và đưa ra đánh giá mức độ phù hợp với yêu cầu công việc, hỗ trợ nhân viên tuyển dụng trong bước sàng lọc hồ sơ ban đầu.

4.4. Cơ sở dữ liệu

Hệ thống sử dụng MySQL làm hệ quản trị cơ sở dữ liệu, với tên cơ sở dữ liệu là recruitment_db. MySQL là hệ quản trị cơ sở dữ liệu quan hệ mã nguồn mở, phổ biến, có độ ổn định cao và phù hợp với các hệ thống quản lý nghiệp vụ có dữ liệu quan hệ rõ ràng như bài toán quản lý tuyển dụng của đề tài.
