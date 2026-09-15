#!/usr/bin/env python3
"""Validate the repository's reviewed Bing site-authentication artifact."""

import argparse
import hashlib
import stat
import sys
from pathlib import Path
from xml.dom import Node, minidom


EXPECTED_MODE = 0o644
EXPECTED_SIZE = 85
EXPECTED_SHA256 = "aaaf16a744091a69345634583dca3f4bf30244830585ca58803d1cb22aed0b40"


class ValidationError(ValueError):
    """The authentication artifact does not match the reviewed binding."""


def validate_xml(payload: bytes) -> None:
    try:
        document = minidom.parseString(payload)
    except Exception as error:
        raise ValidationError("document is not well-formed XML") from error

    if document.doctype is not None:
        raise ValidationError("document types and entities are forbidden")
    forbidden_document_nodes = {
        Node.PROCESSING_INSTRUCTION_NODE,
        Node.COMMENT_NODE,
    }
    if any(node.nodeType in forbidden_document_nodes for node in document.childNodes):
        raise ValidationError("processing instructions and comments are forbidden")

    root = document.documentElement
    if root.tagName != "users" or root.attributes.length:
        raise ValidationError("root must be an attribute-free users element")
    if any(
        node.nodeType == Node.TEXT_NODE and node.data.strip()
        for node in root.childNodes
    ):
        raise ValidationError("root may contain only whitespace and the user element")

    elements = [node for node in root.childNodes if node.nodeType == Node.ELEMENT_NODE]
    if len(elements) != 1 or elements[0].tagName != "user":
        raise ValidationError("root must contain exactly one user element")
    if any(
        node.nodeType not in (Node.TEXT_NODE, Node.ELEMENT_NODE)
        for node in root.childNodes
    ):
        raise ValidationError("comments, CDATA, and processing instructions are forbidden")

    leaf = elements[0]
    if leaf.attributes.length:
        raise ValidationError("user element must not have attributes")
    if len(leaf.childNodes) != 1 or leaf.childNodes[0].nodeType != Node.TEXT_NODE:
        raise ValidationError("user must contain one nonempty text leaf and no nested nodes")
    if not leaf.childNodes[0].data.strip():
        raise ValidationError("user leaf must not be empty")


def validate(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValidationError("path must be a regular, non-symlink file")

    metadata = path.stat()
    mode = stat.S_IMODE(metadata.st_mode)
    if mode != EXPECTED_MODE:
        raise ValidationError(f"mode must be {EXPECTED_MODE:04o}, got {mode:04o}")

    payload = path.read_bytes()
    if len(payload) != EXPECTED_SIZE:
        raise ValidationError(f"size must be {EXPECTED_SIZE} bytes, got {len(payload)}")
    if hashlib.sha256(payload).hexdigest() != EXPECTED_SHA256:
        raise ValidationError("content digest does not match the reviewed binding")
    validate_xml(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        validate(args.root / "BingSiteAuth.xml")
    except ValidationError as error:
        print(f"BingSiteAuth integrity check failed: {error}", file=sys.stderr)
        return 1
    print("BingSiteAuth integrity check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
