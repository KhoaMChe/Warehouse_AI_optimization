# Warehouse AI - Tối ưu vị trí đặt hàng trong kho

## Tổng quan

Dự án này xây dựng một quy trình phân tích dữ liệu kho để hỗ trợ tối ưu vị trí đặt hàng của SKU trong kho. Mục tiêu là kết hợp dữ liệu tồn kho, xuất kho, nhập kho và châm hàng để tạo bộ đặc trưng, từ đó xác định kho hoặc vị trí phù hợp nhất cho từng sản phẩm.

Dự án hiện được triển khai chủ yếu bằng notebook để khám phá dữ liệu, làm sạch, tạo đặc trưng và thử nghiệm mô hình. Các hàm xử lý lõi được tách ra trong thư mục `src/` để có thể tái sử dụng.

## Bài toán

Trong vận hành kho, một SKU thường có thể xuất hiện ở nhiều vị trí hoặc nhiều kho khác nhau. Nếu không có quy tắc phân bổ tốt, hàng dễ bị dàn trải, làm tăng thời gian picking, gây thiếu hụt cục bộ và giảm hiệu quả châm hàng.

### Mục tiêu chính

- Xây dựng bộ đặc trưng theo SKU từ dữ liệu kho.
- Ước lượng kho chính hoặc vị trí phù hợp cho từng SKU.
- Hỗ trợ ra quyết định sắp xếp hàng hóa để tối ưu thao tác xuất nhập và châm hàng.

## Dữ liệu đầu vào

Dự án sử dụng các bảng dữ liệu nghiệp vụ kho, được lưu ở `data/raw/` và phiên bản đã làm sạch ở `data/clean/`.

### Nhóm dữ liệu chính

- Danh mục sản phẩm: `dm_san_pham`
- Danh mục vị trí: `dm_vi_tri`
- Tồn kho: `xnk_ton_kho`
- Xuất kho: `xnk_xuat_kho`
- Nhập kho: `xnk_nhap_kho`
- Pick list và phiếu pick: `xnk_xuat_kho_pick_list`, `xnk_xuat_kho_phieu_pick`
- Nhật ký châm hàng: `log_replenishment`

## Quy trình xử lý

1. Đọc dữ liệu thô từ thư mục `data/raw/`.
2. Làm sạch, loại cột dư thừa và xử lý giá trị thiếu.
3. Tạo feature theo SKU từ tồn kho, xuất kho và châm hàng.
4. Tạo thêm feature theo vị trí kho.
5. Ghép nhãn kho chính cho mỗi SKU dựa trên tồn kho lớn nhất.
6. Dùng bộ dữ liệu kết quả để phân tích và huấn luyện mô hình.

## Cấu trúc đặc trưng

Các feature hiện được xây dựng trong `src/feature/`:

- `basic.py`: feature cơ bản theo SKU, gồm tồn kho, xuất kho, châm hàng và số lượng vị trí/LPN.
- `advanced.py`: feature dẫn xuất như `inventory_turnover`, `replenishment_ratio`, `pick_density`.
- `warehouse.py`: feature theo vị trí kho.
- `merge.py`: ghép các bảng feature thành một bảng tổng.
- `temporal.py`: feature thời gian theo lịch sử xuất kho.

Dataset nhãn cho bài toán kho chính được tạo trong `src/dataset/dataset.py` bằng cách chọn kho có tổng tồn lớn nhất cho mỗi SKU.

## Cấu trúc thư mục

```text
warehouse-slotting/
│
├── main.py
├── README.md
├── requirements.txt
│
├── data/
│   ├── raw/
│   ├── clean/
│   ├── processed/          ⭐ Feature sau khi tạo
│   └── external/
│
├── notebooks/
│   ├── 01_cleaning.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_training.ipynb
│   └── 05_evaluation.ipynb
│
├── src/
│
│   ├── preprocessing.py
│
│   ├── dataset/
│   │     loader.py
│   │
│   ├── feature/
│   │     __init__.py
│   │     basic.py
│   │     temporal.py
│   │     warehouse.py
│   │     advanced.py
│   │     merge.py
│   │
│   ├── model/
│   │     ranker.py
│   │     rule_based.py
│   │
│   ├── evaluation/
│   │     metrics.py
│   │
│   └── utils.py
│
├── simulation/
│
├── output/
│   ├── feature_table.csv
│   ├── ranking_result.csv
│   └── recommendation.csv
│
└── images/
```

## Hướng dẫn chạy

### 1. Cài đặt môi trường

Tạo môi trường Python và cài các thư viện cần thiết.

### 2. Mở notebook theo thứ tự

- `notebooks/load_and_clean_data.ipynb`: nạp và làm sạch dữ liệu
- `notebooks/feature.ipynb`: tạo feature và dataset huấn luyện
- `notebooks/model.ipynb`: phân tích và thử nghiệm mô hình
- `notebooks/analyze.ipynb`: khám phá dữ liệu và trực quan hóa

### 3. Chạy pipeline dữ liệu

Nếu muốn tái tạo dữ liệu đã xử lý, hãy chạy các notebook làm sạch và feature trước, sau đó dùng các file trong `data/clean/` cho bước phân tích hoặc huấn luyện tiếp theo.

## Kết quả đầu ra

Kết quả của dự án được lưu ở:

- `output/figures/`: biểu đồ, hình minh họa
- `output/reports/`: báo cáo
- `output/tables/`: bảng kết quả

## Ghi chú

- Hiện tại repo thiên về notebook, các file `main.py`, `src/model/model.py`, `src/train/train.py` và `simulation/sim.py` chưa có phần triển khai hoàn chỉnh.
- Các hàm trong `src/` đã được tách riêng để dễ mở rộng sang pipeline tự động sau này.

## Hướng phát triển tiếp

- Hoàn thiện script chạy end-to-end thay vì phụ thuộc notebook.
- Bổ sung mô hình dự đoán kho hoặc vị trí cho SKU.
- Thêm đánh giá hiệu quả trước và sau tối ưu bằng các KPI vận hành kho.
