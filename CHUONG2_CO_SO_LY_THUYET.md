2. CÁC CÔNG NGHỆ VÀ CƠ SỞ LÝ THUYẾT

2.1. Ngôn ngữ Python

2.1.1. Python - ngôn ngữ thông dịch, đa năng

Python là ngôn ngữ lập trình bậc cao, thông dịch (interpreted), có cú pháp ngắn gọn, gần với ngôn ngữ tự nhiên nên dễ đọc và dễ tiếp cận. Python được dùng rộng rãi trong nhiều lĩnh vực khác nhau như phát triển web, xử lý dữ liệu, tự động hóa và đặc biệt là trí tuệ nhân tạo/học máy - đây cũng là một trong những lý do đề tài chọn Python làm ngôn ngữ chính cho backend, vì hệ thống có tích hợp chức năng phân tích CV bằng AI. Python có cộng đồng lập trình viên rất lớn, tài liệu phong phú, giúp việc tra cứu và xử lý sự cố trong quá trình phát triển thuận lợi hơn.

2.1.2. Type Hinting (gợi ý kiểu dữ liệu)

Mặc dù Python vốn là ngôn ngữ định kiểu động (dynamic typing - không bắt buộc khai báo kiểu dữ liệu của biến), Python hiện đại hỗ trợ thêm cơ chế Type Hinting, cho phép khai báo kiểu dữ liệu mong muốn cho biến, tham số hàm và giá trị trả về. Type Hinting không làm thay đổi cách Python thực thi chương trình, nhưng giúp trình soạn thảo code gợi ý chính xác hơn, phát hiện sớm một số lỗi trước khi chạy, và quan trọng hơn - đây chính là cơ chế mà các thư viện như Pydantic và FastAPI dựa vào để tự động kiểm tra và chuẩn hóa dữ liệu, giảm thiểu lỗi phát sinh ở tầng dữ liệu đầu vào/đầu ra của hệ thống.

2.1.3. Quản lý gói và môi trường ảo (pip, venv)

Pip (Package Installer for Python) là công cụ quản lý gói tiêu chuẩn của Python, cho phép cài đặt, gỡ bỏ và quản lý phiên bản của các thư viện bên thứ ba chỉ bằng một dòng lệnh đơn giản. Đi kèm với đó, venv (virtual environment) giúp tạo ra một môi trường Python độc lập cho từng dự án, tách biệt hoàn toàn thư viện và phiên bản Python của dự án này với dự án khác trên cùng một máy, tránh tình trạng xung đột phiên bản gây lỗi khó kiểm soát.

2.1.4. Cross-Platform

Python là ngôn ngữ đa nền tảng - cùng một mã nguồn có thể chạy được trên nhiều hệ điều hành khác nhau như Windows, Linux hay macOS mà không cần chỉnh sửa, miễn là môi trường đích đã được cài đặt trình thông dịch Python phù hợp. Đặc điểm này giúp việc phát triển và triển khai hệ thống linh hoạt hơn, không bị phụ thuộc vào một hệ điều hành cụ thể.

2.1.5. Hệ sinh thái thư viện phong phú

Python sở hữu kho thư viện mã nguồn mở khổng lồ thông qua PyPI (Python Package Index), với hàng trăm nghìn gói thư viện phục vụ hầu như mọi nhu cầu lập trình. Nhờ đó, thay vì phải tự xây dựng từ đầu các phần việc như đọc file PDF/Word, mã hóa mật khẩu hay tạo token đăng nhập, hệ thống có thể tận dụng những thư viện đã được cộng đồng phát triển, kiểm chứng và tối ưu sẵn, giúp rút ngắn đáng kể thời gian phát triển.

2.2. Framework FastAPI

2.2.1. FastAPI - framework xây dựng API bằng Python

FastAPI là một web framework hiện đại của Python, chuyên dùng để xây dựng các API theo kiến trúc RESTful. FastAPI được xây dựng dựa trên Starlette (xử lý phần lõi web/HTTP) và Pydantic (xử lý phần kiểm tra dữ liệu), kết hợp cả hai để mang lại hiệu năng cao trong khi vẫn giữ cú pháp viết code ngắn gọn, rõ ràng. Đây là framework được chọn làm nền tảng chính cho toàn bộ backend của hệ thống, đảm nhiệm việc định nghĩa và xử lý tất cả các API mà giao diện người dùng gọi tới.

2.2.2. Bất đồng bộ (Asynchronous) và ASGI

FastAPI hỗ trợ lập trình bất đồng bộ thông qua chuẩn ASGI (Asynchronous Server Gateway Interface) - đây là chuẩn giao tiếp thế hệ mới giữa ứng dụng Python và server, thay thế cho chuẩn WSGI truyền thống vốn chỉ xử lý được tuần tự từng request một. Với cơ chế bất đồng bộ, trong lúc chờ một tác vụ tốn thời gian như truy vấn cơ sở dữ liệu, gửi email hay gọi sang dịch vụ AI bên ngoài, server vẫn có thể tiếp tục xử lý các request khác thay vì phải đứng im chờ đợi, giúp hệ thống phục vụ được nhiều người dùng cùng lúc hiệu quả hơn.

2.2.3. Dependency Injection

Dependency Injection (tiêm phụ thuộc) là cơ chế cho phép một hàm xử lý API khai báo trước những gì nó cần (ví dụ: một kết nối tới cơ sở dữ liệu, hoặc thông tin người dùng đang đăng nhập), và FastAPI sẽ tự động cung cấp (tiêm vào) những thứ đó mỗi khi hàm được gọi, mà người viết code không cần tự khởi tạo thủ công. Nhờ cơ chế này, các logic dùng chung như kiểm tra đăng nhập, kiểm tra phân quyền theo vai trò hay mở/đóng kết nối cơ sở dữ liệu chỉ cần viết một lần rồi tái sử dụng ở bất kỳ API nào cần đến, giúp mã nguồn gọn gàng và nhất quán hơn.

2.2.4. Pydantic - kiểm tra và chuẩn hóa dữ liệu

Pydantic là thư viện chịu trách nhiệm định nghĩa cấu trúc dữ liệu mà mỗi API nhận vào và trả về, dựa trên cơ chế Type Hinting của Python. Khi có dữ liệu gửi đến, Pydantic sẽ tự động kiểm tra kiểu dữ liệu, các trường bắt buộc, định dạng hợp lệ; nếu dữ liệu không đúng, hệ thống sẽ tự động trả về lỗi rõ ràng cho người dùng trước khi dữ liệu sai có thể đi sâu vào các bước xử lý nghiệp vụ hay chạm tới cơ sở dữ liệu.

2.2.5. Tự động sinh tài liệu API (OpenAPI/Swagger UI)

Nhờ toàn bộ API đã được khai báo rõ ràng kiểu dữ liệu thông qua Pydantic và Type Hinting, FastAPI có thể tự động sinh ra tài liệu API theo chuẩn OpenAPI, hiển thị trực quan qua giao diện Swagger UI. Tài liệu này liệt kê đầy đủ các API hiện có, dữ liệu đầu vào/đầu ra và cho phép gửi thử request ngay trên trình duyệt, hỗ trợ rất nhiều cho quá trình phát triển và kiểm thử hệ thống mà không cần viết tài liệu thủ công riêng.

2.3. SQLAlchemy

2.3.1. Tổng quan về ORM (Object-Relational Mapping)

ORM là kỹ thuật ánh xạ giữa hai mô hình khác nhau: mô hình hướng đối tượng trong code (class, object) và mô hình quan hệ trong cơ sở dữ liệu (bảng, dòng). Thay vì phải viết trực tiếp các câu lệnh SQL dưới dạng chuỗi văn bản, lập trình viên có thể thao tác với dữ liệu thông qua các đối tượng Python quen thuộc - ví dụ một dòng trong bảng ứng viên được biểu diễn như một object với các thuộc tính tương ứng. Cách tiếp cận này giúp mã nguồn dễ đọc, dễ bảo trì hơn, đồng thời hạn chế được rủi ro tấn công SQL Injection vì các giá trị truyền vào truy vấn đều được xử lý an toàn thông qua cơ chế tham số hóa (parameter binding) của ORM thay vì nối chuỗi SQL thủ công.

2.3.2. Tổng quan về SQLAlchemy 2.0

SQLAlchemy là thư viện ORM phổ biến và mạnh mẽ nhất của Python, được hệ thống sử dụng ở phiên bản 2.0. Trong SQLAlchemy, mỗi bảng dữ liệu được định nghĩa bằng một class Python (Declarative Model), mỗi cột là một thuộc tính có khai báo kiểu dữ liệu rõ ràng, và quan hệ giữa các bảng (một-nhiều, nhiều-nhiều) được khai báo tường minh ngay trong class, giúp người đọc code hình dung được cấu trúc cơ sở dữ liệu mà không cần mở trực tiếp công cụ quản trị database. Việc thao tác với dữ liệu (thêm, sửa, xóa, truy vấn) được thực hiện thông qua đối tượng Session - đối tượng quản lý toàn bộ vòng đời của một phiên làm việc với cơ sở dữ liệu, bao gồm cả việc gom nhóm các thay đổi thành một transaction để đảm bảo tính toàn vẹn dữ liệu.

2.4. MySQL

MySQL là hệ quản trị cơ sở dữ liệu quan hệ (RDBMS) mã nguồn mở được sử dụng phổ biến nhất hiện nay. Dữ liệu trong MySQL được tổ chức thành các bảng có quan hệ với nhau thông qua khóa chính (Primary Key) và khóa ngoại (Foreign Key), phù hợp với những hệ thống có cấu trúc dữ liệu rõ ràng, chặt chẽ như bài toán quản lý tuyển dụng của đề tài - nơi các thực thể như Tin tuyển dụng, Hồ sơ ứng tuyển, Ứng viên, Lịch phỏng vấn, Thư mời nhận việc đều có quan hệ ràng buộc lẫn nhau. MySQL đảm bảo tính chất ACID (Atomicity - Nguyên tử, Consistency - Nhất quán, Isolation - Cô lập, Durability - Bền vững) cho các giao dịch, giúp dữ liệu luôn ở trạng thái đúng đắn ngay cả khi có nhiều yêu cầu ghi dữ liệu diễn ra đồng thời. Đây cũng là hệ quản trị cơ sở dữ liệu có cộng đồng sử dụng lớn, tài liệu phong phú và được hầu hết các công cụ, thư viện phổ biến hỗ trợ tốt.

2.5. Xác thực và bảo mật

2.5.1. JWT (JSON Web Token)

JWT là một chuẩn mở dùng để trao đổi thông tin xác thực một cách an toàn giữa các bên dưới dạng một chuỗi token, gồm ba phần: Header (thông tin về thuật toán mã hóa), Payload (dữ liệu như mã người dùng, vai trò, thời gian hết hạn) và Signature (chữ ký dùng để xác minh token không bị giả mạo hay chỉnh sửa). Điểm đặc trưng của JWT là cơ chế xác thực không trạng thái (stateless) - server không cần lưu lại thông tin phiên đăng nhập, mà chỉ cần xác minh chữ ký của token gửi kèm mỗi request là có thể biết được request đó có hợp lệ hay không và thuộc về người dùng nào. Hệ thống sử dụng cặp access token (thời gian sống ngắn, dùng cho từng request) và refresh token (thời gian sống dài hơn, dùng để cấp lại access token mới khi hết hạn) để vừa đảm bảo bảo mật, vừa không bắt người dùng phải đăng nhập lại liên tục.

2.5.2. Băm mật khẩu với Bcrypt

Bcrypt là thuật toán băm (hashing) chuyên dùng để mã hóa mật khẩu một chiều - nghĩa là từ mật khẩu gốc có thể tính ra được chuỗi băm, nhưng không thể tính ngược lại từ chuỗi băm để ra mật khẩu gốc. Khác với các thuật toán băm thông thường như MD5 hay SHA vốn không phù hợp để lưu mật khẩu vì tốc độ tính toán quá nhanh (dễ bị tấn công dò mật khẩu hàng loạt), Bcrypt được thiết kế có độ trễ tính toán có thể điều chỉnh (cost factor) và tự động thêm một đoạn dữ liệu ngẫu nhiên (salt) riêng cho từng mật khẩu trước khi băm, giúp chống lại hiệu quả các kiểu tấn công dò mật khẩu bằng bảng tra sẵn (rainbow table). Nhờ đó, kể cả khi dữ liệu người dùng chẳng may bị lộ, mật khẩu thật của người dùng vẫn được bảo vệ an toàn.

2.6. Các thư viện đã được cài đặt vào hệ thống

2.6.1. Thư viện ở phía client (frontend)

Giao diện người dùng của hệ thống không sử dụng framework frontend riêng biệt mà xây dựng trên nền JavaScript thuần, kết hợp thêm một số thư viện hỗ trợ trình bày và trực quan hóa: Tailwind CSS đảm nhiệm việc thiết kế giao diện nhanh chóng, đồng bộ và tương thích tốt trên nhiều kích thước màn hình; Chart.js dùng để vẽ các biểu đồ thống kê trực quan trên trang Dashboard; Font Awesome cung cấp bộ icon cho các nút bấm, thanh menu; và font chữ Inter (lấy từ Google Fonts) giúp giao diện hiển thị hiện đại, dễ đọc.

2.6.2. Thư viện ở phía server (backend)

Phía backend sử dụng các thư viện đã trình bày ở các mục trên (FastAPI, Uvicorn, SQLAlchemy, Pydantic/Pydantic Settings), cùng với một số thư viện hỗ trợ chuyên biệt khác: email-validator để kiểm tra định dạng email hợp lệ; python-multipart để xử lý dữ liệu tải file lên dạng multipart/form-data; pypdf và python-docx để đọc và trích xuất nội dung văn bản từ file CV định dạng PDF và Word phục vụ chức năng phân tích AI; python-jose để tạo và xác thực token JWT; passlib kết hợp với Bcrypt để băm mật khẩu; pymysql đóng vai trò driver kết nối tới cơ sở dữ liệu MySQL; và Pytest để viết, chạy các kịch bản kiểm thử tự động cho toàn bộ hệ thống trong suốt quá trình phát triển.
