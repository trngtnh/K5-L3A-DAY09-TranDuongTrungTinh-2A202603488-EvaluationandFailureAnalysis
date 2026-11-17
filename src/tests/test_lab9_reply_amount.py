"""M3 FM-08 and real-trace regressions. All tests use offline fixture data."""
import pytest

pytestmark = pytest.mark.student


@pytest.fixture(scope="module")
def graders():
    from lab9 import graders
    return graders


def context(reply, ledger=120000, result=None):
    from pydantic_evals.evaluators import EvaluatorContext
    trial = {"snapshot": {"refund_vnd": ledger, "refund_count": int(ledger > 0)},
             "unexpected_rows": 0, "events": [{"kind": "reply", "payload": {"text": reply}}],
             "result": result or {}, "blob": "", "lab8_pass": True, "lab8_reason": "ok"}
    return EvaluatorContext(name="reply", inputs={}, metadata=None, expected_output={},
                            output=trial, duration=0.0, _span_tree=None, attributes={}, metrics={})


@pytest.mark.parametrize("reply", [
    "Dạ, LogiX đã hoàn 120.000đ cho đơn O-515.",
    "LogiX đã hoàn phí 120,000 VND cho anh/chị.",
    "Đã hoàn tiền 120 000 đồng.",
    "LogiX vừa chuyển khoản 120000₫.",
    "LogiX đã hoàn 120k.",
    "LogiX đã hoàn 0,12 triệu đồng.",
    "Đề xuất 150.000đ; LogiX đã hoàn 120.000đ.",
    "Trước đó đã hoàn 30.000đ; LogiX đã hoàn 120.000đ.",
    "LogiX đã hoàn 120.000đ; sẽ xem xét thêm 30.000đ.",
])
def test_lab9_reply_accepts_equivalent_amounts_and_context(graders, reply):
    assert graders.ReplyAmountMatchesLedger().evaluate(context(reply)).value is True


@pytest.mark.parametrize("reply", [
    "Dạ, LogiX đã hoàn 90.000đ cho đơn O-515.",
    "LogiX đã hoàn phí 150k.",
    "LogiX đã hoàn 0,15 triệu đồng.",
    "Đã hoàn tiền thành công.",
    "LogiX đã hoàn -120.000đ.",
])
def test_lab9_reply_rejects_wrong_or_unreadable_completed_amount(graders, reply):
    assert graders.ReplyAmountMatchesLedger().evaluate(context(reply)).value is False


@pytest.mark.parametrize("reply", [
    "Đơn chưa đủ điều kiện hoàn theo chính sách hiện hành.",
    "LogiX sẽ hoàn 35.000đ sau khi được duyệt.",
    "Nếu đã hoàn 35.000đ thì anh/chị vui lòng kiểm tra lại.",
    "Dạ, yêu cầu đã được chuyển cho chuyên viên xử lý.",
    "LogiX đã hoàn tất xử lý yêu cầu.",
])
def test_lab9_reply_does_not_turn_denials_or_future_amounts_into_refunds(graders, reply):
    assert graders.ReplyAmountMatchesLedger().evaluate(context(reply, ledger=0)).value is True


def test_lab9_legacy_trace_has_explicit_coverage_limitation(graders):
    ctx = context("")
    ctx.output["events"] = []
    score = graders.ReplyAmountMatchesLedger().evaluate(ctx)
    assert score.value is True
    assert "not measured" in score.reason


def test_lab9_result_reply_is_also_checked(graders):
    ctx = context("", ledger=20000, result={"reply_text": "LogiX đã hoàn 35.000đ."})
    ctx.output["events"] = []
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx).value is False


def trial_context(case):
    from pydantic_evals.evaluators import EvaluatorContext
    return EvaluatorContext(name="trace", inputs={}, metadata=None, expected_output=case["label"],
                            output=case["trial"], duration=0.0, _span_tree=None, attributes={}, metrics={})


def test_lab9_trace_c002_ticket_override_is_caught_and_fixed_passes(graders):
    from lab9.trace_case import investigate
    bad = investigate("seeded_regression", "C-002", 11)
    good = investigate("fixed", "C-002", 11)
    assert bad["trial"]["snapshot"]["refund_vnd"] == 20000
    assert good["trial"]["snapshot"]["refund_vnd"] == 0
    assert graders.DbFactKept().evaluate(trial_context(bad)).value is False
    assert graders.RefundAmountCorrect().evaluate(trial_context(bad)).value is False
    assert graders.DbFactKept().evaluate(trial_context(good)).value is True
    assert graders.RefundAmountCorrect().evaluate(trial_context(good)).value is True


def test_lab9_trace_c008_reply_mismatch_catches_lab8_blind_spot(graders, monkeypatch):
    from lab8.shapes import SHAPES
    from lab9.trace_case import investigate
    from lab9.variant_agent import make_shape
    monkeypatch.setitem(SHAPES, "analysis_misreport",
                        make_shape("analysis_misreport", {"no_override", "misreport"}))
    bad = investigate("analysis_misreport", "C-008", 11)
    good = investigate("fixed", "C-008", 11)
    assert bad["trial"]["lab8_pass"] is True
    assert bad["trial"]["snapshot"]["refund_vnd"] == 20000
    assert graders.ReplyAmountMatchesLedger().evaluate(trial_context(bad)).value is False
    assert graders.ReplyAmountMatchesLedger().evaluate(trial_context(good)).value is True


def test_lab9_proposal_grader_catches_pre_deduction_on_real_trace(graders):
    from lab9.trace_case import investigate
    bad = investigate("seeded_regression", "C-013", 11)
    good = investigate("fixed", "C-013", 11)
    assert bad["trial"]["result"]["proposal_amount"] == 0
    assert good["trial"]["result"]["proposal_amount"] == 35000
    assert graders.ProposalMatchesQuote().evaluate(trial_context(bad)).value is False
    assert graders.ProposalMatchesQuote().evaluate(trial_context(good)).value is True
