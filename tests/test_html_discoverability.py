import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_html_discoverability", ROOT / "tools" / "check_html_discoverability.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class HtmlDiscoverabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write("sitemap-index.xml", self.sitemap_index("a.xml"))
        urls = [
            "https://wulfkaal.github.io/",
            "https://wulfkaal.github.io/claims/one",
            "https://wulfkaal.github.io/entities/one",
            "https://wulfkaal.github.io/claims/by-topic/one.html",
            "https://wulfkaal.github.io/positions/one",
        ]
        self.write("a.xml", self.sitemap(urls))
        self.write("style.css", "body {}")
        self.write("index.html", self.page(urls[0], "Root", "Root description", [
            "/claims/one", "/entities/one", "/claims/by-topic/one.html", "/positions/one"
        ]))
        self.write("claims/one.html", self.page(urls[1], "Claim one", "Claim description"))
        self.write("entities/one.html", self.page(urls[2], "Entity one", "Entity description"))
        self.write(
            "claims/by-topic/one.html",
            self.page(urls[3], "Topic one", "Topic description", ["/style.css"]),
        )
        self.write("positions/one.html", self.page(urls[4], "Position one", "Position description"))

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def sitemap_index(*names):
        rows = "".join(
            f"<sitemap><loc>https://wulfkaal.github.io/{name}</loc></sitemap>" for name in names
        )
        return ('<?xml version="1.0"?><sitemapindex '
                'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + rows + "</sitemapindex>")

    @staticmethod
    def sitemap(urls):
        rows = "".join(f"<url><loc>{url}</loc></url>" for url in urls)
        return ('<?xml version="1.0"?><urlset '
                'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + rows + "</urlset>")

    @staticmethod
    def page(canonical, title, description, links=(), extra_head="", json_ld='{"@type":"Thing"}'):
        anchors = "".join(f'<a href="{link}">link</a>' for link in links)
        return (
            "<!doctype html><html><head>"
            f"<title>{title}</title><meta name=\"description\" content=\"{description}\">"
            f'<link rel="canonical" href="{canonical}"><link rel="stylesheet" href="/style.css">'
            f'<script type="application/ld+json">{json_ld}</script>{extra_head}'
            f"</head><body>{anchors}</body></html>"
        )

    def codes(self):
        problems, _ = CHECKER.check(self.root)
        return {problem.split()[0] for problem in problems}, problems

    def test_valid_fixture_passes(self):
        self.assertEqual(self.codes()[1], [])

    def test_unreachable_and_depth_mutations_fail(self):
        index = (self.root / "index.html").read_text(encoding="utf-8")
        self.write("index.html", index.replace('<a href="/claims/one">link</a>', ""))
        codes, _ = self.codes()
        self.assertIn("UNREACHABLE", codes)

        self.write("index.html", self.page("https://wulfkaal.github.io/", "Root", "Root description", ["/hop-1.html"]))
        for number in range(1, 5):
            target = f"/hop-{number + 1}.html" if number < 4 else "/claims/one"
            self.write(f"hop-{number}.html", self.page(
                f"https://wulfkaal.github.io/hop-{number}.html",
                f"Hop {number}", f"Hop description {number}", [target]
            ))
        codes, _ = self.codes()
        self.assertIn("DEPTH", codes)

    def test_canonical_mutations_fail(self):
        path = self.root / "claims/one.html"
        original = path.read_text(encoding="utf-8")
        for mutated, expected in (
            (original.replace('<link rel="canonical" href="https://wulfkaal.github.io/claims/one">', ""), "CANONICAL_COUNT"),
            (original.replace("/claims/one\"", "/claims/wrong\""), "CANONICAL_SELF"),
            (original.replace("<link rel=\"stylesheet\"", '<link rel="canonical" href="https://wulfkaal.github.io/claims/one"><link rel="stylesheet"'), "CANONICAL_COUNT"),
        ):
            self.write("claims/one.html", mutated)
            self.assertIn(expected, self.codes()[0])
        self.write("claims/one.html", original)

    def test_metadata_mutations_fail(self):
        entity = self.root / "entities/one.html"
        original = entity.read_text(encoding="utf-8")
        self.write("entities/one.html", original.replace("Entity description", ""))
        self.assertIn("METADATA_DESCRIPTION", self.codes()[0])
        claim = (self.root / "claims/one.html").read_text(encoding="utf-8")
        self.write("entities/one.html", original.replace("Entity one", "Claim one"))
        self.write("claims/one.html", claim)
        self.assertIn("METADATA_DUPLICATE_TITLE", self.codes()[0])

    def test_each_generated_family_requires_valid_json_ld(self):
        paths = (
            "claims/one.html", "entities/one.html", "claims/by-topic/one.html", "positions/one.html"
        )
        for path in paths:
            with self.subTest(path=path):
                original = (self.root / path).read_text(encoding="utf-8")
                self.write(path, original.replace('{"@type":"Thing"}', "{"))
                self.assertIn("JSON_LD", self.codes()[0])
                self.write(path, original)

    def test_third_party_script_and_subresource_mutations_fail(self):
        page = (self.root / "claims/one.html").read_text(encoding="utf-8")
        for tag in (
            '<script src="https://example.test/x.js"></script>',
            '<img src="https://example.test/x.png">',
        ):
            with self.subTest(tag=tag):
                self.write("claims/one.html", page.replace("</head>", tag + "</head>"))
                self.assertIn("THIRD_PARTY", self.codes()[0])
        self.write("claims/one.html", page)

    def test_multiple_sitemap_owners_fail(self):
        self.write("sitemap-index.xml", self.sitemap_index("a.xml", "b.xml"))
        self.write("b.xml", self.sitemap(["https://wulfkaal.github.io/claims/one"]))
        self.assertIn("SITEMAP_OWNER", self.codes()[0])

    def test_noncanonical_alias_and_missing_page_fail(self):
        a = (self.root / "a.xml").read_text(encoding="utf-8")
        alias = "https://wulfkaal.github.io/entities/one.html"
        self.write("a.xml", a.replace("</urlset>", f"<url><loc>{alias}</loc></url></urlset>"))
        self.assertIn("SITEMAP_ALIAS", self.codes()[0])
        self.write("a.xml", a.replace("/positions/one", "/positions/missing"))
        codes, _ = self.codes()
        self.assertNotIn("SITEMAP_ALIAS", codes)
        self.assertIn("HTML_MISSING", codes)

    def test_broken_advertised_local_link_fails(self):
        page = (self.root / "positions/one.html").read_text(encoding="utf-8")
        self.write("positions/one.html", page.replace("</body>", '<a href="/missing.json">x</a></body>'))
        self.assertIn("LOCAL_LINK", self.codes()[0])

    def test_allowlists_are_exact_and_reason_tagged(self):
        for exceptions in CHECKER.ALLOWLISTS.values():
            for digest, reason in exceptions.items():
                self.assertRegex(digest, r"^[0-9a-f]{64}$")
                self.assertTrue(reason.strip())
        original = CHECKER.ALLOWLISTS["JSON_LD"]
        try:
            detail = "claims/one.html: missing for claim"
            digest = CHECKER.exception_digest([detail])
            CHECKER.ALLOWLISTS["JSON_LD"] = {digest: "fixture legacy exception"}
            page = (self.root / "claims/one.html").read_text(encoding="utf-8")
            self.write(
                "claims/one.html",
                page.replace('<script type="application/ld+json">{"@type":"Thing"}</script>', ""),
            )
            problems, _ = CHECKER.check(self.root)
            self.assertFalse(any(p.startswith("JSON_LD claims/one.html") for p in problems))
            self.assertFalse(CHECKER.pending_is_allowed("JSON_LD", [detail, "entities/one.html: missing for entity"]))
        finally:
            CHECKER.ALLOWLISTS["JSON_LD"] = original

    def test_ci_runs_mutation_suite_and_checker_in_both_validation_jobs(self):
        workflow = (ROOT / ".github" / "workflows" / "corpus-projections.yml").read_text(
            encoding="utf-8"
        )
        self.assertEqual(workflow.count("tests/test_html_discoverability.py"), 2)
        self.assertEqual(
            workflow.count("python3 tools/check_html_discoverability.py --root ."), 2
        )


if __name__ == "__main__":
    unittest.main()
