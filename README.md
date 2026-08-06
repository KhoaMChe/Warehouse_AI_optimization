# Warehouse AI Slotting

Warehouse AI Slotting là hệ thống hỗ trợ quyết định vị trí lưu trữ hàng hóa trong kho. Hệ thống kết hợp mô hình học máy, các ràng buộc vận hành và khoảng cách đường đi ngắn nhất trên mạng lưới lối đi để đề xuất Top 5 vị trí Reserve phù hợp cho một lượt nhập hàng.

Ứng dụng hiện tập trung vào bài toán Putaway: từ thông tin SKU và lô hàng nhập, hệ thống dự đoán khu vực tiềm năng, loại bỏ các vị trí không khả thi và xếp hạng các vị trí còn lại theo chi phí vận hành.

## Mục tiêu

- Đề xuất vị trí Reserve phù hợp thay vì lựa chọn theo thứ tự dữ liệu hoặc quy tắc cố định.
- Giảm quãng đường di chuyển từ khu Receiving đến vị trí lưu trữ.
- Hạn chế phân tán cùng một SKU trên nhiều khu vực.
- Kiểm soát tải trọng, thể tích, trạng thái vị trí và loại vị trí.
- Cân bằng giữa hiệu quả Putaway, Picking và Replenishment.
- Cung cấp kết quả có thể giải thích thông qua từng thành phần điểm.

## Kiến trúc giải pháp

Hệ thống sử dụng kiến trúc hybrid gồm ba lớp.

```text
Warehouse data
    -> Data cleaning
    -> Feature engineering
    -> Reserve-only training dataset
    -> Random Forest models
    -> Aisle graph and distance matrix
    -> Hard-constraint filtering
    -> Multi-factor ranking
    -> Top 5 Reserve locations
```

### Lớp dự đoán

Random Forest được sử dụng để dự đoán:

- `day_ke_id`: dãy kệ tiềm năng.
- `tang`: tầng phù hợp theo từng dãy được dự đoán.

Mô hình được huấn luyện riêng theo kho và chỉ sử dụng dữ liệu vị trí Reserve. Khi chạy với model cũ có feature `tang` trong bài toán dự đoán dãy, predictor tổng hợp xác suất theo phân bố tầng Reserve thực tế của kho để tránh lấy ngẫu nhiên tầng từ một dòng lịch sử.

### Lớp ràng buộc

Trước khi chấm điểm, hệ thống loại bỏ các vị trí:

- Không thuộc kho đang xử lý.
- Không thuộc loại Reserve, mặc định `vi_tri_type_id = 2`.
- Đã bị xóa hoặc không hoạt động.
- Đang chứa SKU khác.
- Không còn đủ tải trọng hoặc thể tích cho một đơn vị lưu trữ.

Các ràng buộc cứng luôn được áp dụng trước điểm số của mô hình.

### Lớp tối ưu khoảng cách

Kho được biểu diễn bằng một aisle graph:

- Các rack được bố trí song song.
- Các vị trí trên cùng rack được nối theo thứ tự bay.
- Các aisle được nối qua cross-aisle phía dưới và phía trên.
- Bảy cổng Receiving được nối với main aisle.
- Sáu cổng Shipping được nối với main aisle.
- Transit/Staging Area được đặt bên phải kho.
- Xe nâng chỉ di chuyển trên các cạnh của graph và không đi xuyên qua rack.

Khoảng cách được tính bằng multi-source Dijkstra thay vì khoảng cách Euclidean. Hệ thống sinh các feature:

- `inbound_distance_m`: đường ngắn nhất từ cổng nhập gần nhất.
- `outbound_distance_m`: đường ngắn nhất tới cổng xuất gần nhất.
- `staging_distance_m`: đường ngắn nhất tới khu staging.
- `same_sku_distance_m`: đường ngắn nhất tới một vị trí đang chứa cùng SKU.

### Lớp xếp hạng

Điểm cuối cùng kết hợp:

- Xác suất từ mô hình dự đoán dãy và tầng.
- Ưu tiên vị trí đang chứa cùng SKU.
- Ưu tiên vị trí trống.
- Mức đáp ứng sức chứa.
- Khoảng cách tới cùng SKU.
- Khoảng cách từ Receiving.
- Khoảng cách tới Shipping.
- Độ phù hợp của tầng với trọng lượng, thể tích và hạn sử dụng.
- Mức độ tắc nghẽn của dãy.

Trọng số khoảng cách được điều chỉnh theo nhóm ABC. SKU xuất nhanh ưu tiên đường tới Shipping nhiều hơn; SKU xuất chậm ưu tiên giảm chi phí Putaway từ Receiving.

## Cấu trúc dự án

```text
warehouse AI/
    app.py
    README.md
    requirements.txt

    data/
        raw/              Dữ liệu nguồn
        clean/            Dữ liệu đã làm sạch
        process/          Feature table và training dataset

    models/
        <kho_id>/
            RandomForest/
            ExtraTrees/
            LightGBM/
            CatBoost/
            benchmark.csv

    src/
        feature/
            feature.py    Tạo feature tồn, xuất, ABC, châm hàng và thời gian
            merge.py      Ghép feature sản phẩm với vị trí lịch sử

        model/
            train.py              Điều phối huấn luyện theo kho
            trainer.py            Chia tập, huấn luyện và đánh giá
            predictor.py          Nạp model và dự đoán dãy, tầng
            ranking.py            Lọc candidate và xếp hạng vị trí
            warehouse_graph.py    Aisle graph và shortest-path distance
            test.py               Kịch bản kiểm tra thủ công

    Rules/
        basic_rules.py
        business_rules.py
        rule_engine.py
        rule_ranking.py

    database/
        setup_database.py         Schema và tiện ích SQLite
        setupsmss.py              Thiết lập SQL Server
        slap_schema_mssql.sql     Schema SQL Server
        importdata.py             Nhập dữ liệu vào database

    notebooks/                    EDA, làm sạch và thử nghiệm
    tests/
        test_slotting.py          Kiểm thử ranking và aisle graph
    output/
        figures/                  Biểu đồ phân tích
```

## Dữ liệu đầu vào

### Danh mục sản phẩm

File mặc định: `data/clean/dm_san_pham_clean.csv`

Các trường quan trọng:

| Trường | Ý nghĩa |
|---|---|
| `auto_id` | ID sản phẩm |
| `nganh_hang_id` | Ngành hàng |
| `gw_san_pham` | Trọng lượng của đơn vị lưu trữ |
| `cbm_san_pham` | Thể tích của đơn vị lưu trữ |
| `so_ngay_su_dung` | Thời hạn sử dụng |
| `sl_cai_1_thung` | Số sản phẩm trong một thùng |
| `sl_thung_1_pallet` | Số thùng trên một pallet |

### Danh mục vị trí

File mặc định: `data/clean/dm_vi_tri_clean.csv`

| Trường | Ý nghĩa |
|---|---|
| `auto_id` | ID vị trí |
| `kho_id` | ID kho |
| `day_ke_id` | ID dãy kệ |
| `ma_so_vi_tri` | Mã vị trí |
| `tang` | Tầng |
| `vi_tri_seq_id` | Thứ tự bay trong dãy |
| `vi_tri_type_id` | Loại vị trí |
| `gw_max` | Tải trọng tối đa |
| `cbm_max` | Thể tích tối đa |
| `trang_thai_id` | Trạng thái hoạt động |
| `deleted` | Cờ xóa dữ liệu |

### Tồn kho

File mặc định: `data/clean/xnk_ton_kho_clean.csv`

Dữ liệu tồn được tổng hợp theo `vi_tri_id` và `san_pham_id`. Lượng tồn thực được ước tính bằng tổng nhập cộng điều chỉnh trừ tổng xuất. Các dòng có lượng tồn không dương không được dùng để xác định vị trí đang bị chiếm dụng.

### Feature table

File mặc định: `data/process/classic_feature.csv`

Feature chính gồm:

- Tổng nhập, tổng xuất và tồn kho.
- Tần suất xuất.
- Nhóm và điểm ABC.
- Tỷ lệ châm hàng.
- Vòng quay tồn kho.
- Trọng lượng và thể tích sản phẩm.
- Thời hạn sử dụng và tuổi tồn kho.
- Dãy, tầng và loại vị trí lịch sử.

## Quy ước đơn vị

Đơn vị phải được chuẩn hóa trước khi sử dụng trong production:

- `gw_san_pham` và `gw_max` phải cùng đơn vị, khuyến nghị kilogram.
- `cbm_san_pham`, `cbm_max` và dữ liệu tồn phải cùng đơn vị thể tích.
- `tong_nhap` trong giao diện hiện được dùng làm hệ số nhân với trọng lượng và thể tích sản phẩm.

Do đó, số lượng nhập phải có cùng cấp đóng gói với `gw_san_pham` và `cbm_san_pham`. Nếu hai trường này mô tả một thùng thì số lượng nhập phải là số thùng. Không nên đưa hệ thống vào vận hành tự động trước khi xác nhận quy ước này với dữ liệu nghiệp vụ.

## Cài đặt

Yêu cầu Python 3.10 trở lên.

```bash
python -m venv .venv
```

Trên Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install streamlit plotly lightgbm catboost
```

Trên Linux hoặc macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
pip install streamlit plotly lightgbm catboost
```

## Chạy ứng dụng

Từ thư mục gốc dự án:

```bash
streamlit run app.py
```

Ứng dụng chỉ hiển thị các kho có đủ model Random Forest cho cả `day_ke_id` và `tang`.

Quy trình sử dụng:

1. Chọn kho.
2. Chọn SKU có sẵn hoặc khai báo SKU mới.
3. Nhập số ngày sử dụng còn lại.
4. Nhập số lượng theo đúng đơn vị đóng gói.
5. Yêu cầu hệ thống gợi ý vị trí.
6. Kiểm tra Top 5 cùng các khoảng cách và thành phần điểm.

## Huấn luyện model

Mở `src/model/train.py` và cấu hình:

```python
KHO_ID = 12630825
```

Sau đó chạy từ thư mục `src/model` để các đường dẫn dữ liệu tương đối hoạt động đúng:

```bash
cd src/model
python train.py
```

Pipeline huấn luyện:

- Chỉ lấy dữ liệu Reserve của kho được chọn.
- Loại `tang` khỏi feature dự đoán `day_ke_id` để tránh quan hệ vòng.
- Chia train/test theo SKU bằng `GroupShuffleSplit` để hạn chế data leakage.
- Huấn luyện và so sánh Random Forest, Extra Trees, LightGBM và CatBoost.
- Lưu model, danh sách feature, feature importance và benchmark theo kho.

Model mà ứng dụng đang sử dụng phải nằm tại:

```text
models/<kho_id>/RandomForest/day_ke_id.pkl
models/<kho_id>/RandomForest/day_ke_id_columns.pkl
models/<kho_id>/RandomForest/tang.pkl
models/<kho_id>/RandomForest/tang_columns.pkl
```

## Cấu hình warehouse graph

Các tham số mặc định nằm trong `WarehouseGraphConfig`:

| Tham số | Mặc định | Ý nghĩa |
|---|---:|---|
| `inbound_gate_count` | 7 | Số cổng nhập |
| `outbound_gate_count` | 6 | Số cổng xuất |
| `rack_spacing_m` | 4.0 | Khoảng cách giữa các aisle |
| `bay_spacing_m` | 1.2 | Khoảng cách giữa hai bay |
| `gate_apron_m` | 6.0 | Khoảng cách từ cổng đến main aisle |
| `staging_offset_m` | 8.0 | Khoảng cách từ staging đến aisle bên phải |
| `floor_handling_m` | 1.5 | Chi phí tương đương cho mỗi tầng nâng |
| `include_top_cross_aisle` | `True` | Cho phép đi qua cross-aisle phía trên |

Các khoảng cách mặc định là giả định kỹ thuật. Trước khi triển khai thực tế, cần thay bằng kích thước đo từ bản vẽ kho và ánh xạ chính xác vị trí của 13 cổng.

## Kiểm thử

Chạy toàn bộ kiểm thử từ thư mục gốc:

```bash
python -m unittest discover -s tests -v
```

Bộ kiểm thử hiện kiểm tra:

- Chỉ trả về vị trí Reserve.
- Loại vị trí không đủ sức chứa tối thiểu.
- Thứ tự kết quả ổn định khi các vị trí đồng điểm.
- Đường đi giữa hai rack phải qua cross-aisle, không xuyên qua rack.
- Graph có đủ bảy cổng nhập và sáu cổng xuất.

## Database

Dự án cung cấp hai lựa chọn lưu trữ:

- SQLite thông qua `database/setup_database.py`.
- SQL Server thông qua `database/setupsmss.py` và `database/slap_schema_mssql.sql`.

Schema bao gồm dữ liệu nguồn, thống kê SKU, distance, lịch sử chạy thuật toán và kết quả gán vị trí. Thông tin kết nối SQL Server nên được truyền bằng biến môi trường `MSSQL_CONN`; không lưu mật khẩu trực tiếp trong source.

## Đánh giá mô hình và vận hành

Accuracy và F1 chỉ đánh giá khả năng tái hiện vị trí lịch sử. Khi đánh giá hiệu quả slotting, cần bổ sung các KPI vận hành:

- Quãng đường Putaway trung bình.
- Quãng đường Picking trung bình.
- Quãng đường Replenishment.
- Tỷ lệ sử dụng thể tích và tải trọng.
- Số vị trí trên mỗi SKU.
- Tỷ lệ đề xuất bị nhân viên từ chối.
- Tỷ lệ vi phạm constraint.
- Thời gian sinh đề xuất.

Trước khi tự động gán vị trí, hệ thống nên được chạy ở chế độ hỗ trợ quyết định hoặc shadow mode để so sánh đề xuất với quyết định thực tế của nhân viên kho.

## Giới hạn hiện tại

- Tọa độ cổng và kích thước aisle đang được suy ra từ cấu hình, chưa lấy từ bản vẽ CAD hoặc khảo sát thực tế.
- Chưa mô hình hóa đầy đủ đường một chiều, khu vực cấm, điểm quay đầu và tốc độ xe nâng theo từng đoạn.
- Capacity chưa phân bổ một lô nhập lớn qua nhiều vị trí.
- FEFO, FIFO, lot, chủ hàng và điều kiện bảo quản chưa phải hard constraint hoàn chỉnh.
- Model học từ lịch sử vận hành nên không tự đảm bảo lịch sử đó là phương án tối ưu.

## Hướng phát triển

1. Chuẩn hóa đơn vị sản phẩm, thùng, pallet, trọng lượng và thể tích.
2. Nhập tọa độ rack, bay, cross-aisle, staging và từng cổng từ bản vẽ thực tế.
3. Bổ sung cạnh một chiều và thời gian di chuyển thay cho khoảng cách đơn thuần.
4. Phân bổ một lượt nhập qua nhiều vị trí bằng Mixed Integer Programming hoặc min-cost flow.
5. Triển khai FEFO/FIFO và các constraint tương thích hàng hóa.
6. Backtest theo thời gian và đánh giá bằng KPI vận hành.
7. Ghi nhận quyết định chấp nhận hoặc override để huấn luyện learning-to-rank trong tương lai.

## Phạm vi sử dụng

Phiên bản hiện tại phù hợp cho nghiên cứu, thử nghiệm và hỗ trợ quyết định trong pilot. Kết quả không nên được dùng để tự động xác nhận Putaway trong môi trường production cho đến khi đơn vị dữ liệu, sơ đồ kho và toàn bộ constraint nghiệp vụ đã được kiểm chứng.
