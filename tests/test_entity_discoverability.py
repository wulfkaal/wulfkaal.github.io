import collections
import html.parser
import importlib.util
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://wulfkaal.github.io"
MAX_HUB_PAGES = 32
MAX_ENTITY_LINKS_PER_HUB = 200
MAX_HUB_BYTES = 64 * 1024
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_html_discoverability", ROOT / "tools" / "check_html_discoverability.py"
)
CHECKER = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(CHECKER)


class PageParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.canonicals = []
        self.json_ld = []
        self._json_ld_parts = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href"))
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._json_ld_parts = []

    def handle_data(self, data):
        if self._json_ld_parts is not None:
            self._json_ld_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._json_ld_parts is not None:
            self.json_ld.append("".join(self._json_ld_parts))
            self._json_ld_parts = None


def parse_page(path):
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class EntityDiscoverabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads((ROOT / "entities" / "index.json").read_text())
        cls.entities = {entry["slug"]: entry for entry in cls.index["entities"]}

    def test_root_to_hubs_to_every_sitemap_entity(self):
        root = parse_page(ROOT / "index.html")
        self.assertIn("./claims/index.html", root.links)
        claims = parse_page(ROOT / "claims" / "index.html")
        self.assertIn("../entities/index.html", claims.links)

        pending = collections.deque([ROOT / "entities" / "index.html"])
        seen_pages = set()
        linked_slugs = []
        while pending:
            page = pending.popleft().resolve()
            self.assertTrue(page.is_relative_to((ROOT / "entities").resolve()))
            if page in seen_pages:
                continue
            seen_pages.add(page)
            self.assertLessEqual(len(seen_pages), MAX_HUB_PAGES)
            self.assertLessEqual(page.stat().st_size, MAX_HUB_BYTES)
            parsed = parse_page(page)
            entity_links = []
            for href in parsed.links:
                target = (page.parent / urlparse(href).path).resolve()
                if target.name == "index.html" or target.name.startswith("page-"):
                    if target.suffix == ".html":
                        pending.append(target)
                if target.parent == (ROOT / "entities").resolve():
                    slug = target.stem
                    if target.suffix == ".html" and slug in self.entities:
                        entity_links.append(slug)
            self.assertLessEqual(len(entity_links), MAX_ENTITY_LINKS_PER_HUB)
            linked_slugs.extend(entity_links)

        self.assertGreater(len(seen_pages), 1)
        self.assertEqual(len(linked_slugs), len(set(linked_slugs)))
        self.assertEqual(set(linked_slugs), set(self.entities))

        sitemap = ET.parse(ROOT / "sitemap-entities.xml")
        locs = {
            element.text for element in sitemap.iter()
            if element.tag == "loc" or element.tag.endswith("}loc")
        }
        sitemap_slugs = {
            urlparse(url).path.removeprefix("/entities/").removesuffix(".html")
            for url in locs
            if url.startswith(f"{BASE}/entities/") and url.endswith(".html")
        }
        self.assertEqual(sitemap_slugs, set(self.entities))

    def test_every_sitemap_entity_is_within_three_root_clicks(self):
        sitemap = ET.parse(ROOT / "sitemap-entities.xml")
        entity_pages = set()
        for element in sitemap.iter():
            if not (element.tag == "loc" or element.tag.endswith("}loc")) \
                    or not element.text \
                    or urlparse(element.text).path in ("/entities", "/entities/"):
                continue
            candidates = CHECKER.candidates_for(ROOT, element.text, html_only=True)
            self.assertEqual(len(candidates), 1, element.text)
            entity_pages.add(candidates[0])

        depths = {ROOT / "index.html": 0}
        pending = collections.deque(depths)
        cache = {}
        while pending:
            page = pending.popleft()
            if depths[page] == 3:
                continue
            for href in CHECKER.parse_page(page, cache).anchors:
                target, is_local = CHECKER.local_target(ROOT, page, href)
                if is_local and target is not None and target.suffix == ".html" \
                        and target not in depths:
                    depths[target] = depths[page] + 1
                    pending.append(target)

        missing = sorted(entity_pages - set(depths))
        self.assertEqual(
            len(missing), 0,
            f"{len(missing)} sitemap entity page(s) exceed depth 3, e.g. "
            f"{[page.relative_to(ROOT).as_posix() for page in missing[:5]]}",
        )
        self.assertLessEqual(max(depths[page] for page in entity_pages), 3)

    def test_every_entity_sitemap_url_matches_its_page_canonical(self):
        sitemap = ET.parse(ROOT / "sitemap-entities.xml")
        sitemap_urls = [
            element.text for element in sitemap.iter()
            if (element.tag == "loc" or element.tag.endswith("}loc"))
        ]
        expected_pages = {
            ROOT / "entities" / f"{slug}.html" for slug in self.entities
        }
        expected_pages.add(ROOT / "entities" / "index.html")
        mapped_pages = []

        for sitemap_url in sitemap_urls:
            parsed_url = urlparse(sitemap_url)
            self.assertEqual((parsed_url.scheme, parsed_url.netloc),
                             ("https", "wulfkaal.github.io"))
            self.assertFalse(parsed_url.params or parsed_url.query or parsed_url.fragment)
            relative_path = parsed_url.path.removeprefix("/")
            page = ROOT / relative_path
            if parsed_url.path.endswith("/"):
                page /= "index.html"
            mapped_pages.append(page)
            with self.subTest(sitemap_url=sitemap_url):
                self.assertIn(page, expected_pages)
                self.assertTrue(page.is_file())
                self.assertEqual(parse_page(page).canonicals, [sitemap_url])

        self.assertEqual(len(mapped_pages), len(set(mapped_pages)))
        self.assertEqual(set(mapped_pages), expected_pages)

    def test_entity_pages_have_exact_canonical_breadcrumbs_and_json_ld(self):
        for slug, record in self.entities.items():
            with self.subTest(slug=slug):
                page = parse_page(ROOT / "entities" / f"{slug}.html")
                self.assertEqual(page.canonicals,
                                 [f"{BASE}/entities/{slug}.html"])
                self.assertIn("../", page.links)
                self.assertIn("../claims/", page.links)
                self.assertIn("./", page.links)
                self.assertEqual(len(page.json_ld), 1)
                data = json.loads(page.json_ld[0])
                self.assertEqual(data["@context"], "https://schema.org")
                self.assertEqual(data["@type"], "DefinedTerm")
                self.assertEqual(data["@id"], record["url"])
                self.assertEqual(data["identifier"], f"kaal:entity:{slug}")
                self.assertEqual(data["name"], record["name"])
                self.assertEqual(data["url"], record["url"])
                self.assertEqual(data["additionalProperty"], [
                    {
                        "@type": "PropertyValue",
                        "name": "status",
                        "value": record["status"],
                    },
                    {
                        "@type": "PropertyValue",
                        "name": "claim_count",
                        "value": record["claim_count"],
                    },
                    {
                        "@type": "PropertyValue",
                        "name": "work_count",
                        "value": record["work_count"],
                    },
                ])


if __name__ == "__main__":
    unittest.main()
