from __future__ import annotations

from planer.parser import parse_program_text


def test_out_of_scope_block_does_not_swallow_later_starting_domains() -> None:
    txt = """
In scope assets:
zellepay.com

Out of scope vulnerabilities
Out of scope
Denial of service attacks
Please note the Zellepay Facebook page (https://www.facebook.com/zellepay)

Starting Domains
partners.zellepay.com
register.zellepay.com
"""
    parsed = parse_program_text(txt, {})
    domains = set(parsed.get("domains") or [])
    out = set(parsed.get("out_of_scope_targets") or [])

    assert "partners.zellepay.com" in domains
    assert "register.zellepay.com" in domains
    assert "www.facebook.com" in out
    assert "partners.zellepay.com" not in out
