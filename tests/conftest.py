import pikepdf
import pytest


@pytest.fixture
def make_pdf():
    def make(path, password=None):
        path.parent.mkdir(parents=True, exist_ok=True)
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page()
        if password is None:
            pdf.save(path)
        else:
            pdf.save(path, encryption=pikepdf.Encryption(owner="owner-secret", user=password))
        pdf.close()
        return path

    return make
