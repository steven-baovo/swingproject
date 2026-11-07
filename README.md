# Swing Project

Web tiếng Việt hỗ trợ quan sát VN30, xu hướng VNINDEX, thông tin doanh nghiệp và tin kinh tế. Không kết nối tài khoản chứng khoán, không có chức năng đặt lệnh và không cần API key TCBS.

## Hiện trạng

- Có bảng kỹ thuật 30 mã, MA20/50, ATR14, khối lượng tương đối và sức mạnh tương đối so với VNINDEX.
- Có báo cáo theo ngày, nguồn dữ liệu và cảnh báo dữ liệu cũ.
- Hồ sơ cơ bản mới có một phần TCB, FPT, HPG, MSN, VPB, MCH, MWG, GAS, ACB, BSR, VRE, VJC và VIC. Các mã khác hiển thị thiếu dữ liệu.
- Tin kinh tế là tiêu đề và liên kết nguồn; chưa có phân tích tác động tự động.
- Có phép thử lịch sử cho bộ lọc xu hướng. Chiến lược vào và thoát lệnh vẫn cần kiểm chứng.

## Kiểm tra bộ lọc xu hướng

Đối chiếu riêng giai đoạn 13/05–31/07/2026 bằng cách thay MCH và TCX bằng PLX và TPB trong bản sao dữ liệu dùng cho mô phỏng. Hai chuỗi bổ sung từ Entrade khớp cả 204 ngày với VN-Index. Với thời gian giữ 10 phiên, chi phí giả định 0,5% và yêu cầu thoát trước khi kỳ cơ cấu mới có hiệu lực, bản dựng lại có 49 lượt, trung bình −2,45% sau chi phí. Dùng rổ hiện tại trên cùng khoảng ngày cho 48 lượt, trung bình −2,40%. Đây là bản dựng từ các thay đổi đã biết, chưa đối soát toàn bộ 30 thành phần từng phiên. Ngày 13/05 được chọn vì BSR thay DGC từ mốc này. [Công bố của BSR](https://bsr.com.vn/vi/web/bsr/w/co-phieu-bsr-chinh-thuc-lot-ro-vn30-tu-13-5-2026)

Điều kiện tại lúc đóng cửa là VN-Index trên MA50, giá cổ phiếu trên MA50 và MA20 của cổ phiếu trên MA50. Phép thử giả định vào ở giá mở cửa phiên sau và thoát ở giá mở cửa sau số phiên nắm giữ đã chọn. Mỗi mã chỉ có một lượt mô phỏng đang mở. Các lượt của những mã khác nhau có thể trùng thời gian.

```sh
python3 scripts/check_strategy.py --holding-sessions 10 --round-trip-cost-pct 0.5
python3 scripts/check_strategy.py --from-date 2026-07-17 --holding-sessions 10
python3 scripts/check_strategy.py --from-date 2026-08-03 --exit-below-ma50 --match-fixed-entries
```

Trên mẫu 204 phiên kết thúc ngày 06/11/2026, với chi phí giả định 0,5% cho cả lượt mua bán:

| Phiên nắm giữ | Số lượt | Lợi nhuận ròng bình quân mỗi lượt | Chênh lệch với VN-Index |
|---:|---:|---:|---:|
| 5 | 196 | −0,88% | −0,18 điểm % |
| 10 | 117 | −1,32% | −0,31 điểm % |
| 20 | 78 | −2,55% | −0,61 điểm % |

Mẫu áp thành phần VN30 hiện tại về quá khứ. Giá chưa được đối soát điều chỉnh cổ tức và chia tách. Mô phỏng chưa tính giới hạn thanh khoản, tỷ trọng vốn hoặc điều kiện cơ bản. Khi thử tham số mới, cần ghi trước giả thuyết và giữ riêng một giai đoạn chưa dùng để chọn tham số. Đánh giá lợi nhuận sau chi phí và mức lỗ cùng tỷ lệ có lãi.

Đã đối chiếu một sự kiện của VJC. Ngày giao dịch không hưởng quyền 16/06/2026, tỷ lệ cổ tức bằng cổ phiếu là 100:30. Mẫu Entrade ghi đóng cửa 15/06 là 141,31 và mở cửa 16/06 là 143,80 theo thang của nguồn. Chênh lệch khoảng +1,76% phù hợp với khả năng giá trước sự kiện đã được điều chỉnh. Chưa có giá đóng cửa gốc chưa điều chỉnh để xác nhận hệ số. Giữ nguyên chuỗi nguồn để tránh điều chỉnh hai lần và không suy rộng kết quả sang mã khác. [Thông báo HOSE ngày 16/06](https://staticfile.hsx.vn/Uploads/UploadDocuments/2470960/20260616%20Tong%20hop%20thong%20tin%20giao%20dich.pdf) · [Thông báo quyền của VSDC](https://vsdc.vn/vi/ad/196637)

Kỳ cơ cấu có hiệu lực 03/08/2026 đưa MCH và TCX vào, thay PLX và TPB. Khi chỉ xét tín hiệu từ ngày này, mẫu còn 47 điểm vào chung. Giữ 10 phiên đạt trung bình −1,59% và thoát sớm theo MA50 đạt −1,45%, sau chi phí giả định. Đây là phép thử thu hẹp theo mốc cơ cấu đã biết. Vẫn cần danh mục chính thức theo từng phiên và giá của các mã đã rời rổ để kiểm tra đầy đủ giai đoạn trước đó. [Thông tin về kỳ cơ cấu](https://tapchikinhtetaichinh.vn/hose-cong-bo-danh-muc-vn30-ky-thang-7-2026-bo-sung-mch-va-tcx-161885.html)

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

Người dùng đã chọn chỉ xem báo cáo trên web, không cần email hoặc Telegram. Supabase, AI và tự động cập nhật hồ sơ cơ bản chưa được tích hợp. Website có thể chạy bản quan sát hiện tại mà không cần các khóa dịch vụ này.
