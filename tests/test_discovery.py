import pytest

from pdf_unlock.discovery import discover


def test_nonrecursive_recursive_and_symlinks(tmp_path, make_pdf):
    top = make_pdf(tmp_path / "top.PDF")
    nested = make_pdf(tmp_path / "space dir" / "nested.pdf")
    (tmp_path / "link.pdf").symlink_to(top)
    (tmp_path / "dirlink").symlink_to(nested.parent, target_is_directory=True)
    assert discover(tmp_path)[0] == [top]
    assert discover(tmp_path, True)[0] == sorted([top, nested])
    assert discover(top)[0] == [top]
    with pytest.raises(ValueError):
        discover(tmp_path / "link.pdf")
