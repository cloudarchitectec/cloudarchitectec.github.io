"""Full internal link scan on built public/ HTML."""

from __future__ import annotations

import pytest

from conftest import load_script_module

check_internal_links = load_script_module("check-internal-links.py")


class TestInternalLinks:
    def test_all_internal_links_resolve(self, built_site):
        broken = check_internal_links.scan_public(built_site, limit=20)
        if broken:
            lines = "\n".join(f"  {p}: {raw} -> {t}" for p, raw, t in broken)
            pytest.fail(f"broken internal links:\n{lines}")

    def test_external_urls_are_well_formed(self, built_site):
        _, bad_external, external_count = check_internal_links.scan_links(built_site, limit=20)
        if bad_external:
            lines = "\n".join(f"  {p}: {raw} ({reason})" for p, raw, reason in bad_external)
            pytest.fail(f"malformed external URLs:\n{lines}")
        assert external_count > 0, "expected at least one external http(s) URL in built site"
