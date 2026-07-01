from agent.study_agent import _mark_covered, _parse_json, _sample_text, _strip_thinking


class TestStripThinking:
    def test_removes_think_block(self):
        assert _strip_thinking("<think>reasoning here</think>Answer") == "Answer"

    def test_no_think_block_unchanged(self):
        assert _strip_thinking("Just an answer") == "Just an answer"


class TestParseJson:
    def test_plain_object(self):
        assert _parse_json('{"score": "correct"}') == {"score": "correct"}

    def test_plain_array(self):
        assert _parse_json('["Topic A", "Topic B"]') == ["Topic A", "Topic B"]

    def test_markdown_fences(self):
        assert _parse_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_thinking_block_stripped(self):
        assert _parse_json('<think>hmm...</think>["Topic"]') == ["Topic"]

    def test_json_embedded_in_text(self):
        raw = 'Here is my evaluation: {"score": "partial"} — hope it helps'
        assert _parse_json(raw) == {"score": "partial"}

    def test_invalid_returns_none(self):
        assert _parse_json("no json here at all") is None


class TestSampleText:
    def test_short_text_returned_whole(self):
        assert _sample_text("short text", total_chars=100) == "short text"

    def test_long_text_includes_start_middle_end(self):
        text = "S" * 2000 + "M" * 2000 + "E" * 2000
        sample = _sample_text(text, total_chars=600, sections=3)
        assert "S" in sample
        assert "M" in sample
        assert "E" in sample

    def test_sample_respects_size_budget(self):
        text = "x" * 100_000
        sample = _sample_text(text, total_chars=4800, sections=3)
        separator_overhead = 2 * len("\n\n[...]\n\n")
        assert len(sample) <= 4800 + separator_overhead


class TestMarkCovered:
    def test_exact_match(self):
        concepts = {"ARP Spoofing": False, "VLANs": False}
        _mark_covered(concepts, ["ARP Spoofing"])
        assert concepts == {"ARP Spoofing": True, "VLANs": False}

    def test_case_and_whitespace_insensitive(self):
        concepts = {"MAC Addresses": False}
        _mark_covered(concepts, ["  mac addresses "])
        assert concepts["MAC Addresses"] is True

    def test_unknown_names_ignored(self):
        concepts = {"A": False}
        _mark_covered(concepts, ["B", None, 42])
        assert concepts == {"A": False}

    def test_empty_list_changes_nothing(self):
        concepts = {"A": False}
        _mark_covered(concepts, [])
        assert concepts == {"A": False}
