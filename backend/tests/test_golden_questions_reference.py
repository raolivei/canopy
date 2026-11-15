"""Parity reports must not pass without an independent, usable reference."""

from unittest.mock import MagicMock

import pytest

from backend.models.golden_questions import GoldenQuestionsRunResponse
from backend.services.golden_questions import GoldenQuestionsService


@pytest.mark.parametrize("stop_on_failure, expected", [(False, 10), (True, 1)])
def test_missing_reference_is_reported_as_unavailable(stop_on_failure, expected):
    db = MagicMock()
    report = GoldenQuestionsService(db).run_golden_questions(stop_on_failure=stop_on_failure)

    validated = GoldenQuestionsRunResponse(**report)
    assert validated.total_questions == expected
    assert validated.failed == expected
    assert validated.passed == 0
    assert validated.pass_rate == 0
    assert len(validated.errors) == expected
    assert all(result.match_type == "unavailable" for result in validated.results)
    db.execute.assert_not_called()


def test_provider_failure_does_not_fall_back_or_expose_exception(capsys):
    client = MagicMock(side_effect=RuntimeError("private-provider-response"))
    report = GoldenQuestionsService(MagicMock(), client).run_golden_questions(verbose=True)

    assert report["passed"] == 0
    assert report["failed"] == 10
    assert all(result["match_type"] == "unavailable" for result in report["results"])
    assert "private-provider-response" not in str(report)
    assert "private-provider-response" not in capsys.readouterr().out


def test_comparison_error_is_included_in_denominator():
    service = GoldenQuestionsService(MagicMock(), MagicMock())
    service._monarch_answer = MagicMock(return_value=100)
    service._net_worth_canopy = MagicMock(return_value=100)
    service._spending_this_month_canopy = MagicMock(side_effect=ValueError("private-record"))

    report = service.run_golden_questions(stop_on_failure=True)

    assert report["total_questions"] == 2
    assert report["passed"] == 1
    assert report["failed"] == 1
    assert report["pass_rate"] == 0.5
    assert report["results"][1]["match_type"] == "error"
    assert "private-record" not in str(report)


def test_independent_mismatch_still_fails():
    service = GoldenQuestionsService(MagicMock(), lambda *_: {"accounts": [{"current_balance": 80}]})
    service._net_worth_canopy = MagicMock(return_value=100)

    report = service.run_golden_questions(stop_on_failure=True)

    assert report["failed"] == 1
    assert report["results"][0]["match_type"] == "numerical_delta"
    assert report["results"][0]["numerical_delta"] == 20
