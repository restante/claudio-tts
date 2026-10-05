from claudio_tts.markdown import clean


def test_plain_text_passes_through():
    assert clean("Hello there.") == "Hello there."


def test_emphasis_and_links_keep_their_words():
    assert clean("This is **bold**, *soft* and [a link](https://x.io/a).") == (
        "This is bold, soft and a link."
    )


def test_code_is_dropped():
    out = clean("Run `npm test` now.\n\n```bash\nrm -rf /\n```\n\nDone.")
    assert "npm" not in out and "rm" not in out
    assert out.endswith("Done.")


def test_headings_become_sentences_and_lists_flatten():
    out = clean("# Result\n\n- first\n- second\n")
    assert out.splitlines() == ["Result.", "first", "second"]


def test_bare_urls_are_spoken_as_link():
    assert clean("See https://example.com/very/long/path?q=1 for more") == "See link for more"


def test_html_comments_and_emoji_vanish():
    assert clean("Hi <!-- hidden --> there \U0001f389") == "Hi there"


def test_tables_read_row_by_row():
    out = clean("| a | b |\n|---|---|\n| 1 | 2 |\n")
    assert "1, 2." in out
