from nasty._util.misc import chunked


class TestChunked:
    def test_length_divisible(self) -> None:
        assert [[0, 1, 2], [3, 4, 5]] == list(chunked(3, range(6)))

    def test_length_divisible_pad(self) -> None:
        assert [[0, 1, 2], [3, 4, 5]] == list(chunked(3, range(6), pad=True))

    def test_length_not_divisible(self) -> None:
        assert [[0, 1, 2], [3, 4, 5], [6]] == list(chunked(3, range(7)))

    def test_length_not_divisible_pad(self) -> None:
        assert [[0, 1, 2], [3, 4, 5], [6, None, None]] == list(
            chunked(3, range(7), pad=True)
        )

    def test_length_not_divisible_pad_value(self) -> None:
        assert [[0, 1, 2], [3, 4, 5], [6, "x", "x"]] == list(
            chunked(3, range(7), pad=True, pad_value="x")
        )
