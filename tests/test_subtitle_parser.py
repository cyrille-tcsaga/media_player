from core.subtitle_parser import parse_srt


def test_parse_valid_srt_file(tmp_path):
    srt_path = tmp_path / "valid.srt"
    srt_path.write_text(
        "1\n"
        "00:00:01,000 --> 00:00:04,000\n"
        "Hello world\n"
        "\n"
        "2\n"
        "00:00:05,500 --> 00:00:07,250\n"
        "Second line\n"
        "with more text\n",
        encoding="utf-8",
    )

    entries = parse_srt(srt_path)

    assert len(entries) == 2
    assert entries[0].start_ms == 1000
    assert entries[0].end_ms == 4000
    assert entries[0].text == "Hello world"
    assert entries[1].start_ms == 5500
    assert entries[1].end_ms == 7250
    assert entries[1].text == "Second line\nwith more text"


def test_parse_latin1_encoded_srt_file(tmp_path):
    srt_path = tmp_path / "latin1.srt"
    content = "1\n00:00:01,000 --> 00:00:02,000\nCafé, déjà vu\n"
    srt_path.write_bytes(content.encode("latin-1"))

    entries = parse_srt(srt_path)

    assert len(entries) == 1
    assert entries[0].text == "Café, déjà vu"


def test_parse_malformed_srt_returns_partial_valid_entries(tmp_path):
    srt_path = tmp_path / "malformed.srt"
    srt_path.write_text(
        "1\n"
        "not a valid timecode\n"
        "Broken entry\n"
        "\n"
        "2\n"
        "00:00:05,000 --> 00:00:06,000\n"
        "Valid entry\n",
        encoding="utf-8",
    )

    entries = parse_srt(srt_path)

    assert len(entries) == 1
    assert entries[0].text == "Valid entry"


def test_parse_empty_file_returns_empty_list(tmp_path):
    srt_path = tmp_path / "empty.srt"
    srt_path.write_text("", encoding="utf-8")

    assert parse_srt(srt_path) == []


def test_parse_nonexistent_file_returns_empty_list(tmp_path):
    assert parse_srt(tmp_path / "does_not_exist.srt") == []
