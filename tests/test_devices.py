from claudio_tts.devices import normalise, pick

DEVICES = [
    (0, "DELL U2723QE"),
    (2, "Claudio’s AirPods Pro"),
    (3, "USB Audio"),
    (7, "MacBook Pro Speakers"),
    (9, "Microsoft Teams Audio"),
    (10, "ZoomAudioDevice"),
]


def test_default_and_empty_mean_system_default():
    assert pick("default", DEVICES) == [None]
    assert pick("", DEVICES) == [None]
    assert pick(None, DEVICES) == [None]


def test_partial_names_match_case_insensitively():
    assert pick("airpods", DEVICES) == [2]
    assert pick("AIRPODS, macbook", DEVICES) == [2, 7]


def test_all_skips_virtual_devices():
    assert pick("all", DEVICES) == [0, 2, 3, 7]


def test_unmatched_falls_back_to_default():
    assert pick("headphones", DEVICES) == [None]


def test_listing_label_is_ignored():
    assert normalise("claudio’s airpods pro (default)") == "claudio’s airpods pro"
    assert pick("usb audio (default)", DEVICES) == [3]
