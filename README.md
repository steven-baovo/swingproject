# Swing Project

Web tiếng Việt hỗ trợ quan sát VN30, xu hướng VNINDEX, thông tin doanh nghiệp và tin kinh tế. Không kết nối tài khoản chứng khoán, không có chức năng đặt lệnh và không cần API key TCBS.

## Hiện trạng

- Có bảng kỹ thuật 30 mã, MA20/50, ATR14, khối lượng tương đối và sức mạnh tương đối so với VNINDEX.
- Có báo cáo theo ngày, nguồn dữ liệu và cảnh báo dữ liệu cũ.
- Hồ sơ cơ bản mới có một phần TCB; các mã khác hiển thị thiếu dữ liệu.
- Tin kinh tế là tiêu đề và liên kết nguồn; chưa có phân tích tác động tự động.
- Chưa kiểm chứng chiến lược, chưa có kết quả backtest hay cam kết tỷ lệ thắng.

## Chạy trên máy

Yêu cầu Python 3.9 trở lên và curl. Không cần cài thư viện bên ngoài.

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory web
```

Mở http://127.0.0.1:8765/.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_market.py
python3 scripts/build_report.py
python3 scripts/fetch_news.py
```

## Triển khai dự kiến

Repository: https://github.com/steven-baovo/swingproject

Vercel: chọn repository này, framework Other, thư mục xuất bản `web`. Cấu hình nằm trong `vercel.json`. Bản hiện tại là trang công khai, chỉ chứa dữ liệu thị trường; không đưa khóa riêng hoặc danh mục cá nhân vào thư mục web.

GitHub Actions có lịch cập nhật 17:17 giờ Việt Nam, thứ Hai đến thứ Sáu, và cho phép chạy thủ công. Lịch có thể chạy trễ. Chỉ lưu báo cáo khi đủ dữ liệu và vượt qua kiểm tra; lỗi nguồn tin tức giữ lại tin cũ, không ngăn cập nhật dữ liệu giá. Cần kiểm tra quyền Actions, lần chạy đầu và việc Vercel tự triển khai commit của bot sau khi kết nối tài khoản. Các phần này chưa được xác nhận hoạt động trên tài khoản thật.

## Giới hạn dữ liệu

Danh sách VN30 lấy từ SSI tại thời điểm tải, giá từ Entrade, tiêu đề kinh tế từ RSS VnExpress. Khả năng truy cập công khai không bảo đảm dịch vụ hoặc quyền tái phân phối. Cần xác minh điều khoản nguồn trước khi mở rộng sử dụng.

Giá đang giữ nguyên đơn vị nguồn; việc điều chỉnh cổ tức, chia tách và lịch sử thành phần VN30 chưa được đối soát. Không dùng dữ liệu hiện tại để tuyên bố kết quả chiến lược lịch sử. Báo cáo cùng ngày được thay thế khi chạy lại.

Supabase, AI, thông báo gửi ra ngoài và tự động cập nhật hồ sơ cơ bản chưa được tích hợp. Website có thể chạy bản quan sát hiện tại mà không cần các khóa dịch vụ này.
