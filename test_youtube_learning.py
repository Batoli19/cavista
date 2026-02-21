from engine.youtube_learning import extract_youtube_video_id


def test_extract_video_id_variants():
    expected = "dQw4w9WgXcQ"
    samples = [
        "dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "watch this https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=43s now",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
    ]
    for sample in samples:
        assert extract_youtube_video_id(sample) == expected


def test_extract_video_id_invalid():
    assert extract_youtube_video_id("") is None
    assert extract_youtube_video_id("not a url") is None
    assert extract_youtube_video_id("https://www.youtube.com/watch?v=short") is None
