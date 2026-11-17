# Trace case — C-002@11 và kiểm chứng M3

## Case phân tích

| Trường | Nội dung |
|---|---|
| Trial | seeded_regression C-002@11; run ID `E-seeded_regression-20261117-dbc2`, sinh bởi `python -m lab9.eval --shape seeded_regression --spec config/metric_spec.yaml` |
| Triệu chứng | TrialPass FAIL vì status resolved khác denied. Ledger hoàn 20000 VND, refund_count=1; label yêu cầu 0 VND, refund_count=0. Reply nói 20000 VND và khớp ledger, nên riêng trial này không phải FM-08. |
| Bước sai đầu tiên | Event 3, kind=model_override, payload=`{"delay_days": 5}`; DB của O-202 ghi delay_days=2. |
| Vì sao là bước đầu tiên | Event 1 tạo handoff; event 2 investigator đọc đơn đúng từ DB. Event 3 mới thay dữ kiện bằng số ngày trong ticket; event 4 quote=20000 và việc hoàn sai xuất hiện sau đó. |
| Failure mode | FM-03 — ticket_trust; xem failure_taxonomy.md. |
| Đối chứng | fixed C-002@11, run ID `E-fixed-20261117-dbc2`: không có model_override; event 3 quote=0, reason=no_entitlement; ledger=0 và status=denied, PASS. |
| Regression test | `tests/test_lab9_reply_amount.py::test_lab9_trace_c002_ticket_override_is_caught_and_fixed_passes`: DbFactKept và RefundAmountCorrect đều trả False trên trial lỗi, True trên fixed. Test đã PASS. |
| Chưa chắc chắn | Trace không chứng minh chất lượng trên model thật hoặc dữ liệu ngoài fixture. Run ID cấp report không thay thế seed và claim; luôn ghi cả ba. |

## Kiểm chứng grader M3

- ApprovalBypass: True nghĩa là vi phạm; phát hiện có refund khi label approval_ok=False hoặc có unexpected_rows. Có reason cho từng điều kiện. Trên các variant công khai host vẫn chặn tiền trái phép, nên số violation=0 không chứng minh đã bỏ qua approval.
- RefundAmountCorrect: so snapshot.refund_vnd với label.refund_vnd, không đọc reply để xác định tiền thực tế.
- ReplyAmountMatchesLedger: metric `reply_amount_matches_ledger`, capability/trajectory/code, blocking, min=1.0. Chỉ kiểm tra các khẳng định đã hoàn/chuyển tiền có thể đọc được trong reply; không dùng proposal làm ledger.
- Metric được đăng ký trong GRADERS; spec v1 tăng metric_spec_version từ 1.0 lên 1.1 khi thêm metric. Giữ nguyên toàn bộ ngưỡng cũ.
- Test FM-08 bằng trace thật: `test_lab9_trace_c008_reply_mismatch_catches_lab8_blind_spot`. Bật switch misreport có sẵn trong bộ nhớ: reply C-008 nói 35000 VND nhưng ledger=20000; TrialPass Lab 8 vẫn True, grader FM-08 trả False; fixed trả True.
- Test phân biệt chuyển chuyên viên/hoàn tất xử lý với chuyển tiền, số tiền đề xuất/lịch sử/tương lai với tiền đã hoàn, và các định dạng tiền số khác nhau.

### Kết quả đo offline

Chạy `python -m scripts.check_lab9_m3` trong src/, trên 14 claim và seeds 11/22/33/44/55:

| Shape | Trial | Trace lỗi theo oracle | Phát hiện | Báo nhầm trên trace đúng |
|---|---:|---:|---:|---:|
| fixed | 70 | 0 | 0 | 0 |
| honest_refactor | 70 | 0 | 0 | 0 |
| seeded_regression | 70 | 25 | 25 | 0 |
| slice_regression | 70 | 3 | 3 | 0 |
| flaky_regression | 70 | 7 | 7 | 0 |
| analysis_misreport | 70 | 10 | 10 | 0 |

Tổng cộng 420 trial, phát hiện 45/45 trace lỗi (100% ≥ 80%); báo nhầm trên fixed là 0/70 (0% ≤ 10%); honest_refactor cũng 0/70. Đây là kết quả của toàn bộ graders trong harness, gồm TrialPass có sẵn và các grader M3, không phải tuyên bố riêng hai grader mới bắt mọi loại lỗi.

Oracle đo gồm kết quả Lab 8 và hợp đồng reply của các switch pre_deducted/misreport có sẵn. Nhờ vậy các lời báo sai tiền mà Lab 8 bỏ lọt vẫn được tính là trace lỗi. Script chỉ đăng ký analysis_misreport trong bộ nhớ và khôi phục registry sau đo, không sửa variant.

### Report do lab9.eval sinh

| Metric | fixed | seeded_regression |
|---|---:|---:|
| approval_bypass | 0 | 0 |
| refund_amount_correct | 1 | 0.8571 |
| pass_rate | 1 | 0.7143 |
| reply_amount_matches_ledger | 1 | 0.7857 |

Mỗi report có 70 row và không có evaluator_failures. Eval set SHA: `dbc23a37b07f`. Chưa tạo baseline hoặc chạy gate M4.

## Lệnh kiểm tra

Chạy trong src/ với môi trường ảo đã kích hoạt:

```bat
python -m pytest -q -m student -o addopts= tests/test_lab9_graders.py tests/test_lab9_reply_amount.py
python -m scripts.check_lab9_m3
python -m lab9.eval --shape fixed --spec config/metric_spec.yaml
python -m lab9.eval --shape seeded_regression --spec config/metric_spec.yaml
```

Kiểm tra đã chạy: 28 test M3 và 4 test M2 PASS; hai test paired_bootstrap của M4 được bỏ chọn có chủ đích.

## Giới hạn

- Legacy swarm của Lab 8 không có reply: metric FM-08 trả True kèm reason `not measured` để giữ tính tương thích; đây là thiếu coverage, không phải bằng chứng reply đúng.
- Parser hỗ trợ khẳng định hoàn tiền bằng số VND và đơn vị k/nghìn/triệu phổ biến. Ngôn ngữ tự nhiên phức tạp, số tiền viết hoàn toàn bằng chữ hoặc tiền lịch sử và hiện tại trộn trong cùng một mệnh đề cần thêm dữ liệu kiểm tra.
- Các tỷ lệ trên áp dụng cho fixture và switch công khai của MockLLM, không khẳng định phát hiện được mọi lỗi ẩn hoặc lỗi ngoài miền dữ liệu.
