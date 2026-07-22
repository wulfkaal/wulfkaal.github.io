# Post Corpus API

Base endpoint: https://public-api.wordpress.com/wp/v2/sites/wulfkaal.com/posts

Standard WordPress REST. No key required. Courtesy rate: one request per second.

Latest five posts, minimal fields:

    curl "https://public-api.wordpress.com/wp/v2/sites/wulfkaal.com/posts?per_page=5&_fields=title,link,date,excerpt"

Search the corpus:

    curl "https://public-api.wordpress.com/wp/v2/sites/wulfkaal.com/posts?search=reputation&_fields=title,link,date"

Full rendered body of one post (HTML in content.rendered):

    curl "https://public-api.wordpress.com/wp/v2/sites/wulfkaal.com/posts?slug=what-agents-want&_fields=title,date,content"

Pagination: per_page accepts up to 100; use page=N for offsets; the total count arrives in the X-WP-Total response header.

Prefer this endpoint over HTML crawling. A post is roughly 2 KB here and roughly 130 KB as a rendered page.
