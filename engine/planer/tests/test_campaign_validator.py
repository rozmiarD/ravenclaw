from pathlib import Path

from campaign_validator import validate_campaign


def test_validate_campaign_detects_empty_scope(tmp_path: Path):
    p = tmp_path / "campaign.md"
    p.write_text("# Test\n\n## Campaign Scope\n\n## Rules\n", encoding="utf-8")
    out = validate_campaign(p)
    assert out["ok"] is False
    assert "campaign_scope_empty" in out["errors"]


def test_validate_campaign_accepts_simple_scope(tmp_path: Path):
    p = tmp_path / "campaign.md"
    p.write_text(
        "# Test\n\n## Campaign Scope\n- example.com\n- *.example.net\n\n## Rules\n- x\n",
        encoding="utf-8",
    )
    out = validate_campaign(p)
    assert out["ok"] is True
    assert out["valid_targets"] == 2


def test_validate_campaign_accepts_modern_scope_txt_with_domains_and_urls(tmp_path: Path):
    p = tmp_path / "scope.txt"
    p.write_text(
        """
IN SCOPE:
id.oppo.com
https://www.oppo.com/th/store
https://www.opposhop.cn/m/

OUT OF SCOPE:
ads.oppo.com
""",
        encoding="utf-8",
    )
    out = validate_campaign(p)
    assert out["ok"] is True
    assert out["scope_targets"] == 3
    assert out["valid_targets"] == 3


def test_validate_campaign_modern_scope_ignores_reporting_email_domains(tmp_path: Path):
    p = tmp_path / "scope.txt"
    p.write_text(
        """
IN SCOPE:
https://www.oppo.com/th/store

Test Plan
Please use your hacker email alias when testing (h1username@wearehackerone.com)

Session Layer: HTTP Headers
Researchers should add headers to requests such as:
X-HackerOne-Research: [H1 username]
""",
        encoding="utf-8",
    )
    out = validate_campaign(p)
    assert out["ok"] is True
    assert out["scope_targets"] == 1
    assert out["valid_targets"] == 1
