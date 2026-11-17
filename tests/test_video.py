from labo13.video import format_frame_stem, is_within_time_bounds


def test_is_within_time_bounds() -> None:
	assert is_within_time_bounds(5.0, None, None) is True
	assert is_within_time_bounds(1.99, 2, 10) is False
	assert is_within_time_bounds(2.0, 2, 10) is True
	assert is_within_time_bounds(10.0, 2, 10) is False


def test_format_frame_stem() -> None:
	stem: str = format_frame_stem("IMG_1555", 42, 0.7005)
	assert stem == "IMG_1555_f000042_t0.7005"
