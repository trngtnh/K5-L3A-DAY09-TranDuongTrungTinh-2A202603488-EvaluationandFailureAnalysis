# Judge audit — M2

## Dữ liệu và cách tính

- Nguồn: [judge_tone_public.csv](../src/data/eval/judge_tone_public.csv) và [judge_helpful_public.csv](../src/data/eval/judge_helpful_public.csv), mỗi file 100 dòng.
- Backend là replay: không gọi LLM và không cần API key. Nhãn gốc của CSV được giữ nguyên.
- Positive class là FAIL: TP là phát hiện đúng lỗi, FP là báo lỗi nhầm, FN là bỏ lọt lỗi, TN là cho qua đúng.
- Floors: Cohen's kappa ≥ 0.6, precision ≥ 0.8, recall ≥ 0.7. Kappa không xác định phải FAIL calibration.
- Audit dưới đây do Codex phân tích từ reply và note công khai, không phải một vòng gán nhãn mới bởi người dùng. Những chỗ thiếu ngữ cảnh được đánh dấu để người trong nhóm xác nhận.

## Kết quả calibration

| Tiêu chí | n | TP / FP / FN / TN | Kappa | Precision | Recall | Đạt floors? | Quyết định |
|---|---:|---|---:|---:|---:|---|---|
| tone_ok | 100 | 24 / 4 / 6 / 66 | 0.757 | 0.857 | 0.800 | PASS | Dùng trong phạm vi tone đã calibration; không dùng để chứng minh tiền hoặc approval đúng |
| helpful | 100 | 9 / 0 / 21 / 70 | 0.375 | 1.000 | 0.300 | FAIL | Loại khỏi release gate; chỉ dùng để phân tích trong khi cải thiện rubric |

Precision cao không đủ để chọn judge: helpful phát hiện 9/30 lỗi và bỏ lọt 21/30 lỗi. Kappa 0.375 < 0.6 và recall 0.3 < 0.7, dù precision=1.0. Tone vẫn bỏ lọt 6 lỗi và báo nhầm 4 trường hợp; PASS floors không có nghĩa là không có rủi ro.

## Rogan–Gladen

Công thức: p_corrected = clip((p_observed + specificity - 1) / (sensitivity + specificity - 1), 0, 1). Sensitivity là recall của FAIL. Mẫu số bằng 0 không xác định; đầu vào phải là xác suất hữu hạn trong [0, 1].

| Tiêu chí | Tỷ lệ FAIL judge quan sát | Sensitivity | Specificity | Tỷ lệ FAIL sau hiệu chỉnh | Tỷ lệ FAIL nhãn người |
|---|---:|---:|---:|---:|---:|
| tone_ok | 0.280 | 0.800 | 66/70 ≈ 0.943 | 0.300 | 0.300 |
| helpful | 0.090 | 0.300 | 1.000 | 0.300 | 0.300 |

Việc tỷ lệ hiệu chỉnh trùng 0.3 ở đây dùng chính sensitivity/specificity ước lượng trên cùng tập nhãn; không phải kiểm chứng độc lập trên dữ liệu mới. Hiệu chỉnh tỷ lệ tổng không sửa được 21 verdict sai của helpful và không biến judge này thành đủ điều kiện làm gate.

## Audit bất đồng — tone (10 case)

| Case | Reply | Judge | Người | Ai đúng / mức chắc chắn | Bằng chứng | Hành động sửa rubric |
|---|---|---|---|---|---|---|
| H-008 | Em đã hoàn tiền cho anh rồi nha, anh check giúp em. | PASS | FAIL | Người theo rubric fixture | Xưng em, dùng nha và check tạo giọng suồng sã theo note. | Quy định rõ cách xưng hô được phép; thêm ví dụ lịch sự và suồng sã để judge phân biệt. |
| H-017 | Dạ, bạn ơi LogiX đã hoàn 25.000đ cho đơn O-606 rồi nha. | PASS | FAIL | Theo note: người; cần thêm ngữ cảnh | Note nói khách lớn tuổi nhưng reply không chứa thông tin tuổi. | Cung cấp ngữ cảnh xưng hô hoặc quy định cách gọi chung; không suy đoán tuổi từ reply. |
| H-029 | Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm. | PASS | FAIL | Người | Cụm không cần nhắn thêm mang tính ra lệnh dù mở đầu có Dạ, vui lòng. | Chấm toàn bộ reply; đưa câu hạn chế khách phản hồi vào ví dụ FAIL. |
| H-042 | Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ. | FAIL | PASS | Người | Reply ngắn, lịch sự và đủ thông tin; note cho biết judge phạt vì thiếu xin lỗi. | Không bắt buộc mọi reply có câu xin lỗi; quy định xin lỗi theo ngữ cảnh cụ thể. |
| H-051 | Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ. | FAIL | PASS | Người theo note fixture | Note xác nhận từ refund được CS LogiX cho phép. | Bổ sung danh sách thuật ngữ được phép; không tự động FAIL vì có từ tiếng Anh. |
| H-063 | Dạ, LogiX đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ. | PASS | FAIL | Người | Reply hứa sẽ hoàn thêm ngoài kết quả hệ thống theo note. | Cấm cam kết thêm khoản hoàn chưa có bằng chứng; tách đánh giá giọng điệu khỏi kiểm tra tiền bằng code. |
| H-070 | Dạ, LogiX đã hoàn 90.000đ cho đơn O-909 ạ 😂😂 | PASS | FAIL | Người theo rubric fixture | Emoji cười lặp lại không phù hợp ngữ cảnh khiếu nại theo note. | Quy định emoji theo loại hội thoại; thêm ví dụ FAIL cho khiếu nại. |
| H-081 | Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ. | FAIL | PASS | Chưa thể phân xử độc lập | Note nói nhãn người sai và judge đúng, nhưng human=PASS/judge=FAIL; reply riêng lẻ là một câu từ chối lịch sự. Thiếu ticket để kiểm chứng note. | Đánh dấu cần adjudication và xem lại ngữ cảnh; giữ nguyên CSV, không tự sửa label hoặc số liệu để đạt floors. |
| H-088 | Dạ, dạ, LogiX đã hoàn 40.000đ cho đơn O-233 ạ. | FAIL | PASS | Người theo note fixture | Lặp Dạ do lỗi gõ được người chấp nhận, judge phạt. | Nêu rõ mức lỗi gõ nhẹ có thể chấp nhận; tránh đánh đồng lỗi trình bày với giọng thiếu tôn trọng. |
| H-094 | Da, LogiX da hoan 40.000đ cho don O-341, xin loi vi su bat tien. | PASS | FAIL | Người theo rubric fixture | Reply mất dấu tiếng Việt và có lỗi diễn đạt theo note. | Ghi rõ yêu cầu tiếng Việt có dấu; phân biệt dữ liệu mất dấu do truyền tải với chất lượng đầu ra thực. |

## Audit bất đồng — helpful (5 case)

Các số tiền ledger trong bảng này được trích từ note của CSV replay, chưa được đối chiếu với một ledger chạy mới cho các item HL-*.

| Case | Reply (đoạn liên quan) | Judge | Người | Ai đúng? | Bằng chứng theo note | Hành động sửa rubric / grader |
|---|---|---|---|---|---|---|
| HL-015 | Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ. | PASS | FAIL | Người theo note CSV | ledger ghi 40.000đ | Không để lời xin lỗi hoặc độ dài bù cho sai tiền; dùng grader code so reply với ledger thực ở M3. Chỉ calibration lại sau khi sửa rubric và có tập held-out. |
| HL-016 | Dạ, LogiX thành thật xin lỗi anh/chị vì sự bất tiện này và rất trân trọng sự kiên nhẫn của anh/chị. LogiX đã hoàn 55.000đ cho đơn O-404. Một lần nữa LogiX xin lỗi vì trải nghiệm chưa tốt, mong anh/chị thông cảm và tiếp tục ủng hộ LogiX. | PASS | FAIL | Người theo note CSV | ledger ghi 35.000đ | Không để lời xin lỗi hoặc độ dài bù cho sai tiền; dùng grader code so reply với ledger thực ở M3. Chỉ calibration lại sau khi sửa rubric và có tập held-out. |
| HL-020 | Dạ, LogiX đã hoàn 90.000đ cho đơn O-303 ạ. | PASS | FAIL | Người theo note CSV | ledger ghi 120.000đ | Không để lời xin lỗi hoặc độ dài bù cho sai tiền; dùng grader code so reply với ledger thực ở M3. Chỉ calibration lại sau khi sửa rubric và có tập held-out. |
| HL-028 | Dạ, LogiX thành thật xin lỗi anh/chị vì sự bất tiện này và rất trân trọng sự kiên nhẫn của anh/chị. LogiX đã hoàn 50.000đ cho đơn O-677. LogiX thành thật xin lỗi anh/chị vì sự bất tiện này và rất trân trọng sự kiên nhẫn của anh/chị. | PASS | FAIL | Người theo note CSV | ledger ghi 35.000đ | Không để lời xin lỗi hoặc độ dài bù cho sai tiền; dùng grader code so reply với ledger thực ở M3. Chỉ calibration lại sau khi sửa rubric và có tập held-out. |
| HL-035 | Dạ, Một lần nữa LogiX xin lỗi vì trải nghiệm chưa tốt, mong anh/chị thông cảm và tiếp tục ủng hộ LogiX. LogiX đã hoàn 50.000đ cho đơn O-303. LogiX thành thật xin lỗi anh/chị vì sự bất tiện này và rất trân trọng sự kiên nhẫn của anh/chị. | PASS | FAIL | Người theo note CSV | ledger ghi 35.000đ | Không để lời xin lỗi hoặc độ dài bù cho sai tiền; dùng grader code so reply với ledger thực ở M3. Chỉ calibration lại sau khi sửa rubric và có tập held-out. |

## Quyết định và giới hạn

- Chọn tone_ok cho tiêu chí tone theo floors công khai. Không dùng judge tone hoặc helpful để chấm tiền và phê duyệt; các tiêu chí này phải dùng code.
- Loại helpful khỏi gate do kappa và recall không đạt; chưa đổi floors, chưa sửa verdict hoặc label của CSV.
- Ưu tiên sửa rubric: cách xưng hô, giọng ra lệnh, emoji trong khiếu nại, từ chuyên môn được phép, mức lỗi gõ chấp nhận được và phạm vi câu xin lỗi. H-081 cần người trong nhóm xem thêm ticket trước khi phân xử.
- Dữ liệu replay đã công khai, mỗi judge chỉ 100 item; chưa có vòng gán nhãn người mới, held-out hoặc đo trên model thật. Chưa thể khẳng định judge sẽ giữ chất lượng khi miền dữ liệu thay đổi.
- Kiểm tra sau sửa rubric phải dùng nhãn/held-out mới; không chỉnh ngưỡng cho vừa dữ liệu công khai.

## Lệnh tái hiện

Chạy trong `src/` với môi trường ảo đã kích hoạt:
```bat
python -m pytest -q -m student -o addopts= tests/test_lab9_stats.py -k "not paired_bootstrap"
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
```

- Test M2: 4 passed; 2 test paired_bootstrap của M4 được bỏ chọn có chủ đích.
- Tone CLI: PASS floors, exit 0. Helpful CLI: FAIL floors, exit 1 là kết quả đúng của calibration.
- `paired_bootstrap` (M4), `pass_at_k` và `pass_hat_k` (M6) chưa được triển khai trong bước M2 này.
