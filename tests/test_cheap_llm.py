"""Tests for cheap_llm.py and the extractor switch in scrape_utils.py. No network."""

import io
import json
import urllib.error
from unittest.mock import patch

import pytest

import cheap_llm
import scrape_utils
from cheap_llm import (
    CheapLLMError,
    build_request_body,
    call_cheap_llm,
    call_cheap_llm_with_usage,
    estimate_cost_usd,
)
from eval_extraction_models import COMPARED_FIELDS, compare_extracts, fields_agree, summarize


def _reply(text='{"distance_mi": 100}', usage=None, finish="stop", model="thinkingmachines/inkling-2-mini"):
    return {
        "model": model,
        "choices": [{"message": {"content": text}, "finish_reason": finish}],
        "usage": usage if usage is not None else {"prompt_tokens": 10_000, "completion_tokens": 1_000},
    }


def _http_error(code):
    return urllib.error.HTTPError(cheap_llm.OPENROUTER_URL, code, "err", {}, io.BytesIO(b""))


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    for name in ("CHEAP_LLM_MODEL", "CHEAP_LLM_PROVIDERS", "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SCRAPE_EXTRACTOR"):
        monkeypatch.delenv(name, raising=False)


class TestRequestBody:
    def test_excludes_hosts_that_keep_prompts(self):
        body = build_request_body("hi", "m", 100, True)
        assert body["provider"] == {"data_collection": "deny"}
        assert body["response_format"] == {"type": "json_object"}
        assert body["usage"] == {"include": True}

    def test_pinned_providers_disable_fallback(self, monkeypatch):
        monkeypatch.setenv("CHEAP_LLM_PROVIDERS", "Alpha, Beta ,")
        provider = build_request_body("hi", "m", 100, False)["provider"]
        assert provider["order"] == ["Alpha", "Beta"]
        assert provider["allow_fallbacks"] is False

    def test_json_mode_off_omits_response_format(self):
        assert "response_format" not in build_request_body("hi", "m", 100, False)

    def test_reasoning_effort_is_sent_only_when_asked(self):
        assert "reasoning" not in build_request_body("hi", "m", 100, True)
        assert build_request_body("hi", "m", 100, True, "low")["reasoning"] == {"effort": "low"}

    def test_model_env_override(self, monkeypatch):
        assert cheap_llm.model_id() == cheap_llm.DEFAULT_MODEL
        monkeypatch.setenv("CHEAP_LLM_MODEL", "other/model")
        assert cheap_llm.model_id() == "other/model"


class TestCost:
    def test_price_table_matches_listed_rate(self):
        cost = estimate_cost_usd("thinkingmachines/inkling-2-mini",
                                 {"prompt_tokens": 10_000, "completion_tokens": 1_000})
        assert cost == pytest.approx(0.00105)

    def test_reported_cost_wins(self):
        assert estimate_cost_usd("thinkingmachines/inkling-2-mini", {"cost": 0.5, "prompt_tokens": 1}) == 0.5

    def test_unknown_model_without_reported_cost_is_unknown(self):
        assert estimate_cost_usd("nobody/unknown", {"prompt_tokens": 5}) is None


class TestCall:
    def test_missing_key_fails_loudly(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY")
        with pytest.raises(CheapLLMError, match="OPENROUTER_API_KEY"):
            call_cheap_llm("hi", script="t")

    def test_returns_text_and_usage(self):
        with patch.object(cheap_llm, "_post", return_value=_reply()) as post:
            text, usage = call_cheap_llm_with_usage("hi", script="t")
        assert text == '{"distance_mi": 100}'
        assert usage["model"] == "thinkingmachines/inkling-2-mini"
        assert usage["cost_usd"] == pytest.approx(0.00105)
        assert post.call_args[0][1] == "test-key"

    def test_retries_then_succeeds(self):
        with patch.object(cheap_llm, "_post", side_effect=[_http_error(429), _reply()]) as post, \
             patch.object(cheap_llm.time, "sleep") as sleep:
            assert call_cheap_llm("hi", script="t") == '{"distance_mi": 100}'
        assert post.call_count == 2
        sleep.assert_called_once()

    def test_auth_error_is_not_retried(self):
        with patch.object(cheap_llm, "_post", side_effect=_http_error(401)) as post, \
             patch.object(cheap_llm.time, "sleep"):
            with pytest.raises(CheapLLMError, match="401"):
                call_cheap_llm("hi", script="t")
        assert post.call_count == 1

    def test_gives_up_after_max_retries(self):
        with patch.object(cheap_llm, "_post", side_effect=_http_error(503)) as post, \
             patch.object(cheap_llm.time, "sleep"):
            with pytest.raises(CheapLLMError, match="after 3 attempts"):
                call_cheap_llm("hi", script="t")
        assert post.call_count == 3

    def test_error_object_in_200_is_retried(self):
        with patch.object(cheap_llm, "_post", side_effect=[{"error": {"message": "upstream down"}}, _reply()]), \
             patch.object(cheap_llm.time, "sleep"):
            assert call_cheap_llm("hi", script="t")

    def test_truncated_reply_is_an_error(self):
        with patch.object(cheap_llm, "_post", return_value=_reply(finish="length")):
            with pytest.raises(CheapLLMError, match="cut off"):
                call_cheap_llm("hi", script="t")

    def test_empty_reply_is_an_error(self):
        with patch.object(cheap_llm, "_post", return_value=_reply(text="  ")):
            with pytest.raises(CheapLLMError, match="empty"):
                call_cheap_llm("hi", script="t")

    def test_no_cost_log_without_supabase(self):
        with patch.object(cheap_llm, "_post", return_value=_reply()), \
             patch.object(cheap_llm.urllib.request, "urlopen") as urlopen:
            call_cheap_llm("hi", script="t")
        urlopen.assert_not_called()

    def test_cost_log_row(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://db.example")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "svc")
        with patch.object(cheap_llm, "_post", return_value=_reply()), \
             patch.object(cheap_llm.urllib.request, "urlopen") as urlopen:
            call_cheap_llm("hi", script="scrape_official_sites")
        request = urlopen.call_args[0][0]
        row = json.loads(request.data)
        assert request.full_url == "https://db.example/rest/v1/gg_api_usage"
        assert row == {"provider": "openrouter", "model": "thinkingmachines/inkling-2-mini",
                       "tokens_in": 10_000, "tokens_out": 1_000, "cost_usd": 0.00105,
                       "script": "scrape_official_sites"}

    def test_cost_log_failure_does_not_break_the_call(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://db.example")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "svc")
        with patch.object(cheap_llm, "_post", return_value=_reply()), \
             patch.object(cheap_llm.urllib.request, "urlopen", side_effect=OSError("down")):
            assert call_cheap_llm("hi", script="t")


class TestExtractorSwitch:
    def test_default_is_claude(self, monkeypatch):
        assert scrape_utils.default_extractor() == "claude"
        monkeypatch.setenv("SCRAPE_EXTRACTOR", "Inkling")
        assert scrape_utils.default_extractor() == "inkling"
        monkeypatch.setenv("SCRAPE_EXTRACTOR", "gpt")
        assert scrape_utils.default_extractor() == "claude"

    def test_inkling_path_records_model_and_cost(self):
        with patch.object(cheap_llm, "_post", return_value=_reply('```json\n{"distance_mi": 62}\n```')) as post:
            facts = scrape_utils.extract_race_facts("<html>100 km</html>", "Test Fondo", {}, extractor="inkling")
        # Reasoning shares the output cap; the low-effort, 8,000-token setting keeps the JSON from being cut off.
        body = post.call_args[0][0]
        assert body["max_tokens"] == 8000 and body["reasoning"] == {"effort": "low"}
        assert facts == {"distance_mi": 62, "extraction_model": "thinkingmachines/inkling-2-mini",
                         "extraction_cost_usd": pytest.approx(0.00105)}

    def test_claude_path_unchanged(self):
        with patch("youtube_enrich.call_api", return_value='{"distance_mi": 62}') as call_api, \
             patch.object(cheap_llm, "_post") as post:
            facts = scrape_utils.extract_race_facts_via_claude("<html></html>", "Test Fondo")
        call_api.assert_called_once()
        post.assert_not_called()
        assert facts == {"distance_mi": 62, "extraction_model": "claude-sonnet-4-20250514"}

    def test_failure_returns_error_not_facts(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY")
        facts = scrape_utils.extract_race_facts("<html></html>", "Test Fondo", {}, extractor="inkling")
        assert set(facts) == {"error"}

    def test_non_object_reply_is_an_error(self):
        with patch.object(cheap_llm, "_post", return_value=_reply("[1, 2]")):
            facts = scrape_utils.extract_race_facts("<html></html>", "Test Fondo", {}, extractor="inkling")
        assert set(facts) == {"error"}

    def test_unknown_extractor(self):
        assert "error" in scrape_utils.extract_race_facts("<html></html>", "x", {}, extractor="gpt")


class TestEvalComparison:
    def test_numbers_within_rounding_agree(self):
        assert fields_agree(100, 102)
        assert not fields_agree(100, 110)
        assert fields_agree(0, 0)

    def test_text_is_case_and_space_insensitive(self):
        assert fields_agree("Sold  Out", "sold out")
        assert not fields_agree("open", "closed")

    def test_null_only_agrees_with_null(self):
        assert fields_agree(None, "")
        assert not fields_agree(None, 5)

    def test_verdict_kinds(self):
        ref = {"next_edition_date": "2026-06-06", "distance_mi": 100, "elevation_ft": None, "location": "Girona"}
        cand = {"next_edition_date": "2026-06-07", "distance_mi": 101, "elevation_ft": 5000, "location": None}
        verdicts = compare_extracts(ref, cand)
        assert verdicts["next_edition_date"] == "differ"
        assert verdicts["distance_mi"] == "agree"
        assert verdicts["elevation_ft"] == "candidate_extra"
        assert verdicts["location"] == "candidate_missing"
        assert set(verdicts) == set(COMPARED_FIELDS)

    def test_summary_counts_errors_and_cost(self):
        agree = {f: "agree" for f in COMPARED_FIELDS}
        half = {**agree, "next_edition_date": "differ"}
        summary = summarize([
            {"slug": "a", "verdicts": agree, "candidate_cost_usd": 0.001},
            {"slug": "b", "verdicts": half, "candidate_cost_usd": 0.002},
            {"slug": "c", "candidate_error": "boom"},
        ])
        assert summary["cases"] == 3 and summary["scored"] == 2
        assert summary["candidate_errors"] == 1 and summary["reference_errors"] == 0
        assert summary["per_field"]["next_edition_date"]["agreement"] == 0.5
        assert summary["overall_agreement"] == round(13 / 14, 3)
        assert summary["candidate_cost_usd"] == 0.003

    def test_reference_model_runs_through_openrouter_and_restores_env(self, monkeypatch):
        import eval_extraction_models as ev
        monkeypatch.setenv("CHEAP_LLM_MODEL", "keep/me")
        monkeypatch.setattr(ev, "get_cached", lambda url: {"html": "<html>100 km</html>"})
        seen = []

        def fake_post(body, api_key, timeout):
            seen.append(body["model"])
            return _reply('{"distance_mi": 62}', model=body["model"])

        with patch.object(cheap_llm, "_post", side_effect=fake_post), \
             patch("youtube_enrich.call_api") as call_api:
            case = ev.run_case("x", {"url": "https://x.example", "name": "X"}, reference_model="ref/model")
        call_api.assert_not_called()
        assert seen == ["ref/model", "keep/me"]
        assert cheap_llm.model_id() == "keep/me"
        assert case["reference_model"] == "ref/model"
        assert case["verdicts"]["distance_mi"] == "agree"

    def test_summary_with_nothing_scored(self):
        summary = summarize([{"slug": "c", "candidate_error": "boom"}])
        assert summary["overall_agreement"] is None
        assert summary["per_field"]["next_edition_date"]["agreement"] is None
