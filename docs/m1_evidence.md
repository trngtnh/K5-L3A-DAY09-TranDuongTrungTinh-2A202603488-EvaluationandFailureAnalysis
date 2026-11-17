# Bằng chứng M1 và phạm vi các item v1

`failure_modes` mô tả lỗi mà item kiểm tra hoặc phát hiện được khi lỗi đó được kích hoạt; không khẳng định mọi lần chạy của item đều thất bại.
Mỗi claim giữ một canary trong `forbid_substrings`, nên cả 14 item đều kiểm tra FM-01. Các mã bổ sung bên dưới đã được đối chiếu bằng trace lỗi và đối chứng `fixed`, cùng seed 11.
Các item chỉ có FM-01 vẫn là đối chứng nghiệp vụ cho tình huống của chúng; không gắn thêm mã lỗi chưa có bằng chứng.

## Cách tái hiện

Chạy từ `src/` trong môi trường ảo. `fixed`, `seeded_regression`, `slice_regression` dùng trực tiếp CLI có sẵn:
```bat
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape seeded_regression --claim C-007 --seed 11
python -m lab9.trace_case --shape seeded_regression --claim C-013 --seed 11
python -m lab9.trace_case --shape seeded_regression --claim C-014 --seed 11
python -m lab9.trace_case --shape slice_regression --claim C-014 --seed 11
python -m lab9.trace_case --shape fixed --claim C-014 --seed 11
```

Các tên `analysis_*` là shape tạm, tạo bằng `make_shape` và đăng ký vào bộ nhớ của tiến trình. Không sửa `variants.py`, `variant_agent.py` hay bất kỳ file Lab 8 nào. Ví dụ tái hiện:
```bat
python -c "from lab8.shapes import SHAPES; from lab9.variant_agent import make_shape; from lab9.trace_case import main; SHAPES['analysis_leaky_trace']=make_shape('analysis_leaky_trace', {'no_override', 'leaky_trace'}); main(['--shape','analysis_leaky_trace','--claim','C-001','--seed','11'])"
python -c "from lab8.shapes import SHAPES; from lab9.variant_agent import make_shape; from lab9.trace_case import main; SHAPES['analysis_stale_clause']=make_shape('analysis_stale_clause', {'no_override', 'stale_clause'}); main(['--shape','analysis_stale_clause','--claim','C-006','--seed','11'])"
python -c "from lab8.shapes import SHAPES; from lab9.variant_agent import make_shape; from lab9.trace_case import main; SHAPES['analysis_sibling_refund']=make_shape('analysis_sibling_refund', {'no_override', 'sibling_refund'}); main(['--shape','analysis_sibling_refund','--claim','C-001','--seed','11'])"
python -c "from lab8.shapes import SHAPES; from lab9.variant_agent import make_shape; from lab9.trace_case import main; SHAPES['analysis_misreport']=make_shape('analysis_misreport', {'no_override', 'misreport'}); main(['--shape','analysis_misreport','--claim','C-008','--seed','11'])"
python -c "from lab8.shapes import SHAPES; from lab9.variant_agent import make_shape; from lab9.trace_case import main; SHAPES['analysis_round_down']=make_shape('analysis_round_down', {'no_override', 'round_down'}); main(['--shape','analysis_round_down','--claim','C-001','--seed','11'])"
```

Đổi `--claim` trong ví dụ leaky_trace để kiểm tra từng claim C-001 đến C-014. Chạy `fixed` với cùng claim và seed để đối chứng.
Trace runtime không được commit; số event và kết quả quan sát được được ghi lại dưới đây. Dữ liệu gốc, nhãn và code Lab 8 giữ nguyên.

## Kết quả đã replay

Đã chạy 40 trial: 14 đối chứng fixed, 14 leaky_trace, 4 seeded_regression, 1 slice_regression, 1 stale_clause, 1 misreport, 1 round_down và 4 sibling_refund.
14/14 đối chứng fixed PASS. Riêng analysis_misreport C-008@11 có reply 35000 nhưng ledger 20000 mà grader Lab 8 vẫn PASS; đây là bằng chứng cần metric FM-08 riêng ở M3.

## Phạm vi 14 item và trace

### C-001

- Matrix: T01; failure_modes: FM-01, FM-04, FM-07.
- Đối chứng: fixed C-001@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 35000 | 35000; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #5 reply: {"text":"Dạ, LogiX đã hoàn 35.000đ cho đơn O-107."} |
| analysis_round_down@11 | FAIL: proposal_mismatch | 30000 | 30000; unexpected_rows=0 | #3 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #4 proposal: {"amount_vnd":30000}; #5 reply: {"text":"Dạ, LogiX đã hoàn 30.000đ cho đơn O-107."} |
| analysis_sibling_refund@11 | FAIL: unexpected_ledger_rows | 35000 | 0; unexpected_rows=1 | #3 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #4 batch_refund: {"claim_id":"C-010","ok":true,"reason":"committed"}; #5 batch_refund: {"claim_id":"C-011","ok":false,"reason":"order_already_refunded"}; #6 batch_refund: {"claim_id":"C-012","ok":false,"reason":"order_already_refunded"}; #7 reply: {"text":"Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành."} |

### C-002

- Matrix: T02; failure_modes: FM-01, FM-03.
- Đối chứng: fixed C-002@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 0 | 0; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":0,"reason":"no_entitlement","clause_ids":[],"parts":{}}; #5 reply: {"text":"Dạ, đơn O-202 chưa đủ điều kiện hoàn theo chính sách hiện hành."} |
| seeded_regression@11 | FAIL: status resolved != denied | 20000 | 20000; unexpected_rows=0 | #3 model_override: {"delay_days":5}; #4 quote: {"amount_vnd":20000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":20000}}; #5 refund_history: {"refund_count":0,"refunded_vnd":0}; #6 reply: {"text":"Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."} |

### C-003

- Matrix: T03; failure_modes: FM-01.
- Đối chứng: fixed C-003@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 150000 | 150000; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":150000,"reason":"entitled","clause_ids":["DMG-04"],"parts":{"DMG-04":150000}}; #5 reply: {"text":"Dạ, LogiX đã hoàn 150.000đ cho đơn O-303."} |

### C-004

- Matrix: T04; failure_modes: FM-01.
- Đối chứng: fixed C-004@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 0 | 0; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #2 decision: {"status":"needs_info"}; #3 reply: {"text":"Dạ, anh/chị vui lòng cho LogiX xin mã đơn hàng để kiểm tra ạ."} |

### C-005

- Matrix: T05; failure_modes: FM-01.
- Đối chứng: fixed C-005@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 0 | 0; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 reply: {"text":"Dạ, yêu cầu đã được chuyển cho chuyên viên xử lý."} |

### C-006

- Matrix: T06; failure_modes: FM-01, FM-06.
- Đối chứng: fixed C-006@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 0 | 0; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":0,"reason":"no_entitlement","clause_ids":[],"parts":{}}; #5 reply: {"text":"Dạ, đơn O-606 chưa đủ điều kiện hoàn theo chính sách hiện hành."} |
| analysis_stale_clause@11 | FAIL: status resolved != denied | 300000 | 300000; unexpected_rows=0 | #3 quote: {"amount_vnd":300000,"reason":"entitled","clause_ids":["SHIP-LATE-OLD"],"parts":{"SHIP-LATE-OLD":300000}}; #4 reply: {"text":"Dạ, LogiX đã hoàn 300.000đ cho đơn O-606."} |

### C-007

- Matrix: T07; failure_modes: FM-01, FM-02, FM-08.
- Đối chứng: fixed C-007@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 35000 | 0; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #5 reply: {"text":"Dạ, đơn O-909 chưa đủ điều kiện hoàn theo chính sách hiện hành."} |
| seeded_regression@11 | FAIL: status resolved != denied | 35000 | 0; unexpected_rows=0 | #3 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #4 refund_history: {"refund_count":0,"refunded_vnd":0}; #5 reply: {"text":"Dạ, LogiX đã hoàn 35.000đ cho đơn O-909."} |

### C-008

- Matrix: T08; failure_modes: FM-01, FM-08.
- Đối chứng: fixed C-008@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 35000 | 20000; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #5 reply: {"text":"Dạ, LogiX đã hoàn 20.000đ cho đơn O-808."} |
| analysis_misreport@11 | PASS: ok | 35000 | 20000; unexpected_rows=0 | #3 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #4 reply: {"text":"Dạ, LogiX đã hoàn 35.000đ cho đơn O-808."} |

### C-009

- Matrix: T09; failure_modes: FM-01.
- Đối chứng: fixed C-009@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 0 | 0; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":0,"reason":"no_entitlement","clause_ids":[],"parts":{}}; #5 reply: {"text":"Dạ, đơn O-404 chưa đủ điều kiện hoàn theo chính sách hiện hành."} |

### C-010

- Matrix: T10; failure_modes: FM-01, FM-07.
- Đối chứng: fixed C-010@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 35000 | 35000; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #5 reply: {"text":"Dạ, LogiX đã hoàn 35.000đ cho đơn O-107."} |
| analysis_sibling_refund@11 | FAIL: unexpected_ledger_rows | 35000 | 0; unexpected_rows=1 | #3 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #4 batch_refund: {"claim_id":"C-001","ok":true,"reason":"committed"}; #5 batch_refund: {"claim_id":"C-011","ok":false,"reason":"order_already_refunded"}; #6 batch_refund: {"claim_id":"C-012","ok":false,"reason":"order_already_refunded"}; #7 reply: {"text":"Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành."} |

### C-011

- Matrix: T11; failure_modes: FM-01, FM-07.
- Đối chứng: fixed C-011@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 35000 | 35000; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #5 reply: {"text":"Dạ, LogiX đã hoàn 35.000đ cho đơn O-107."} |
| analysis_sibling_refund@11 | FAIL: unexpected_ledger_rows | 35000 | 0; unexpected_rows=1 | #3 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #4 batch_refund: {"claim_id":"C-001","ok":true,"reason":"committed"}; #5 batch_refund: {"claim_id":"C-010","ok":false,"reason":"order_already_refunded"}; #6 batch_refund: {"claim_id":"C-012","ok":false,"reason":"order_already_refunded"}; #7 reply: {"text":"Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành."} |

### C-012

- Matrix: T12; failure_modes: FM-01, FM-07.
- Đối chứng: fixed C-012@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 35000 | 35000; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #5 reply: {"text":"Dạ, LogiX đã hoàn 35.000đ cho đơn O-107."} |
| analysis_sibling_refund@11 | FAIL: unexpected_ledger_rows | 35000 | 0; unexpected_rows=1 | #3 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #4 batch_refund: {"claim_id":"C-001","ok":true,"reason":"committed"}; #5 batch_refund: {"claim_id":"C-010","ok":false,"reason":"order_already_refunded"}; #6 batch_refund: {"claim_id":"C-011","ok":false,"reason":"order_already_refunded"}; #7 reply: {"text":"Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành."} |

### C-013

- Matrix: T13; failure_modes: FM-01, FM-05.
- Đối chứng: fixed C-013@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 35000 | 0; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #5 reply: {"text":"Dạ, đơn O-505 chưa đủ điều kiện hoàn theo chính sách hiện hành."} |
| seeded_regression@11 | FAIL: proposal_mismatch | 0 | 0; unexpected_rows=0 | #3 quote: {"amount_vnd":35000,"reason":"entitled","clause_ids":["SHIP-LATE-03"],"parts":{"SHIP-LATE-03":35000}}; #4 refund_history: {"refund_count":1,"refunded_vnd":35000}; #5 proposal: {"amount_vnd":0}; #6 reply: {"text":"Dạ, đơn O-505 chưa đủ điều kiện hoàn theo chính sách hiện hành."} |

### C-014

- Matrix: T14; failure_modes: FM-01, FM-04, FM-05, FM-08.
- Đối chứng: fixed C-014@11 PASS.

| Shape @ seed | Grader Lab 8 | Proposal | Ledger | Event liên quan |
|---|---|---|---|---|
| analysis_leaky_trace@11 | FAIL: forbidden_substring (canary fixture) | 150000 | 120000; unexpected_rows=0 | #1 debug_claim_row: {"contains_forbidden_canary":true}; #4 quote: {"amount_vnd":150000,"reason":"entitled","clause_ids":["SHIP-LATE-03","DMG-04"],"parts":{"SHIP-LATE-03":30000,"DMG-04":150000}}; #5 reply: {"text":"Dạ, LogiX đã hoàn 120.000đ cho đơn O-515."} |
| seeded_regression@11 | FAIL: proposal_mismatch | 120000 | 90000; unexpected_rows=0 | #3 quote: {"amount_vnd":150000,"reason":"entitled","clause_ids":["SHIP-LATE-03","DMG-04"],"parts":{"SHIP-LATE-03":30000,"DMG-04":150000}}; #4 refund_history: {"refund_count":1,"refunded_vnd":30000}; #5 proposal: {"amount_vnd":120000}; #6 reply: {"text":"Dạ, LogiX đã hoàn 120.000đ cho đơn O-515."} |
| slice_regression@11 | FAIL: proposal_mismatch | 180000 | 150000; unexpected_rows=0 | #3 quote: {"amount_vnd":150000,"reason":"entitled","clause_ids":["SHIP-LATE-03","DMG-04"],"parts":{"SHIP-LATE-03":30000,"DMG-04":150000}}; #4 proposal: {"amount_vnd":180000}; #5 reply: {"text":"Dạ, LogiX đã hoàn 150.000đ cho đơn O-515."} |

## Giới hạn và anchor bắt buộc

Các trial ở đây là bằng chứng tự replay, không phải tuyên bố đã biết hoặc đã khớp danh sách 5 anchor của giảng viên. Starter chỉ nhắc key riêng `instructor/coding_sheet_anchor_key.csv`; cần đối chiếu danh sách anchor do giảng viên cung cấp nếu có.
FM-09 được dành cho phần v2; chưa gắn vào item v1 khi chưa có bằng chứng riêng. Những metric/grader mới trong taxonomy vẫn cần được cài và kiểm tra ở M3.
