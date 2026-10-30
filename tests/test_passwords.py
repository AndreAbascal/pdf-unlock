from pdf_unlock.passwords import Passwords


def test_unique_memory_only():
    passwords = Passwords()
    for value in ["", "a", "a", "b"]:
        passwords.remember(value)
    assert passwords.values == ["a", "b"]
