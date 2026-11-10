"""Read-only V11 round-trip proof using the original V2 importer and builder.

The trusted HTML is used only in a temporary directory. No source paragraphs,
full HTML, or extracted chapters are written to the public repository.
Usage:
    python -m engine.v2.parity /private/path/v11.html
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .build import ROOT, read_json, render, validate
from .import_v11 import bootstrap


def verify_v11(
    source_path: Path,
    *,
    expected_sha256: str | None = None,
    expected_size_bytes: int | None = None,
) -> dict:
    """Verify an exact round-trip without publishing or retaining source text."""
    source_bytes = Path(source_path).read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    if expected_sha256 is not None and source_sha != expected_sha256:
        raise ValueError(
            f"V11 source SHA-256 mismatch: {source_sha} != {expected_sha256}"
        )
    if expected_size_bytes is not None and len(source_bytes) != expected_size_bytes:
        raise ValueError(
            f"V11 source size mismatch: {len(source_bytes)} != {expected_size_bytes}"
        )

    # The legacy V2 importer intentionally saves full guide chapters and a copy
    # of V11. Redirect every one of its outputs to an automatically removed
    # private workspace; never call it on the public repository root here.
    with TemporaryDirectory(prefix="wow-v11-parity-") as tmp:
        workspace = Path(tmp)
        bootstrap(Path(source_path), destination_root=workspace)
        registry = read_json(workspace / "content" / "registry.json")
        page, guides = render(registry, root=workspace)
        errors = validate(registry, guides, page)
        if errors:
            raise ValueError("V2 HTML structural validation failed: " + "; ".join(errors))
        output_bytes = page.encode("utf-8")
        output_sha = hashlib.sha256(output_bytes).hexdigest()
        if output_bytes != source_bytes:
            raise ValueError(
                f"V11 reconstruction mismatch: generated={output_sha} source={source_sha}"
            )
        chapter_count = sum(len(read_json(
            workspace / "content" / entry["file"]
        )["sections"]) for entry in registry["guides"])

    return {
        "status": "PASS",
        "baseline_sha256": source_sha,
        "reconstructed_sha256": output_sha,
        "size_bytes": len(source_bytes),
        "guide_count": len(guides),
        "chapter_count": chapter_count,
        "byte_identical": True,
        "source_content_published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify byte-identical V11 HTML round-trip")
    parser.add_argument("source", type=Path, help="Private V11 HTML file")
    parser.add_argument(
        "--baseline-manifest",
        type=Path,
        default=ROOT / "docs" / "v2-origin-manifest.json",
        help="Local expected hash/size manifest; original HTML is never uploaded",
    )
    args = parser.parse_args()
    baseline = json.loads(args.baseline_manifest.read_text(encoding="utf-8"))
    result = verify_v11(
        args.source,
        expected_sha256=baseline["v11_baseline_sha256"],
        expected_size_bytes=baseline["v11_baseline_size_bytes"],
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
