# OpenAlex citation snapshot

`citations-openalex.json` is generated from the public OpenAlex API. It is not a hand-edited record.

Check the committed snapshot against live OpenAlex data without writing:

```sh
python3 tools/build_citations_openalex.py --check
```

After reviewed OpenAlex changes, rebuild the snapshot with:

```sh
python3 tools/build_citations_openalex.py
```

The generator writes deterministic field order and formatting. Check mode preserves the committed `fetched_at` value while comparing every generated field, and exits nonzero on drift.
