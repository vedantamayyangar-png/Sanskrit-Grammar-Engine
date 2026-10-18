#!/usr/bin/env python3
"""
Render a range of Sabdamanjari.pdf pages (by book SECTION number, or by raw
PDF page number) to PNG images, for manual/LLM-assisted transcription.

This does NOT do OCR and does NOT produce JSON. Sabdamanjari.pdf has no text
layer (scanned page images) and Devanagari OCR is unreliable for this project's
accuracy bar -- see project_docs/PROJECT_STATE.md. This script only automates
the mechanical step (PDF page -> PNG at a given zoom) so a human or an LLM
with vision can read the pages and transcribe them by hand.

Requires: pypdfium2  (pip install pypdfium2)
On this project's machine, a working Python with pypdfium2 already installed
lives at D:\\python\\python.exe -- a fresh PowerShell session may not have
`python`/`py` on PATH at all (see PROJECT_STATE.md), so prefer:

    D:\\python\\python.exe render_sabdamanjari_pages.py --start-section 5 --end-section 5

Examples:
    # By section number (uses the built-in section -> PDF page map below)
    python render_sabdamanjari_pages.py --start-section 1 --end-section 2

    # By explicit PDF page numbers (1-indexed, inclusive), e.g. for a
    # section not yet in the map, or to re-render a single page at high zoom
    python render_sabdamanjari_pages.py --start-page 34 --end-page 40 --scale 6.0

    # Different source file / output folder
    python render_sabdamanjari_pages.py --source "E:\\Downloads\\Sabdamanjari.pdf" \\
        --start-section 3 --end-section 3 --output "C:\\scratch\\sec3_pages"
"""

import argparse
import sys
from pathlib import Path

# Section -> (start_pdf_page, end_pdf_page), 1-indexed inclusive, PDF page
# numbers (not the book's own printed page numbers). Filled in as sections
# are transcribed -- see sabdamanjari.json / project_docs/CHANGELOG.md.
# Update this table as further sections are discovered.
SECTION_PAGE_MAP = {
    1: (6, 12),    # अजन्त पुंलिङ्ग साधारण शब्दाः
    2: (12, 17),   # अजन्त स्त्रीलिङ्ग साधारण शब्दाः
    3: (17, 21),   # अजन्त नपुंसकलिङ्ग साधारण शब्दाः
    4: (22, 33),   # अजन्त पुंलिङ्ग विशेषशब्दाः (भाग-2 begins)
    # 5: (34, ?)   # अथ अजन्त स्त्रीलिङ्ग विशेष शब्दाः -- end page not yet known;
    #                use --start-page/--end-page for section 5 until this is filled in.
}

DEFAULT_SOURCE = r"E:\Downloads\Sabdamanjari.pdf"
DEFAULT_OUTPUT = r"E:\Sanskrit & Tamil Scholarship\04_Laghu_Siddhanta_Kaumudi\rendered_pages"
DEFAULT_SCALE = 3.0


def resolve_page_range(args) -> tuple[int, int]:
    if args.start_page is not None or args.end_page is not None:
        if args.start_page is None or args.end_page is None:
            sys.exit("Error: --start-page and --end-page must be given together.")
        if args.start_section is not None or args.end_section is not None:
            sys.exit("Error: pass either --start-section/--end-section OR "
                      "--start-page/--end-page, not both.")
        return args.start_page, args.end_page

    if args.start_section is None or args.end_section is None:
        sys.exit("Error: pass --start-section/--end-section OR "
                  "--start-page/--end-page.")

    if args.start_section not in SECTION_PAGE_MAP:
        sys.exit(f"Error: section {args.start_section} is not yet in "
                  f"SECTION_PAGE_MAP (known sections: "
                  f"{sorted(SECTION_PAGE_MAP)}). Add it once its PDF page "
                  f"range is known, or use --start-page/--end-page instead.")
    if args.end_section not in SECTION_PAGE_MAP:
        sys.exit(f"Error: section {args.end_section} is not yet in "
                  f"SECTION_PAGE_MAP (known sections: "
                  f"{sorted(SECTION_PAGE_MAP)}). Add it once its PDF page "
                  f"range is known, or use --start-page/--end-page instead.")

    start_page = SECTION_PAGE_MAP[args.start_section][0]
    end_page = SECTION_PAGE_MAP[args.end_section][1]
    return start_page, end_page


def main():
    parser = argparse.ArgumentParser(
        description="Render Sabdamanjari.pdf pages to PNGs for manual transcription.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--source", default=DEFAULT_SOURCE,
                         help=f"Source PDF path (default: {DEFAULT_SOURCE})")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                         help=f"Output directory for PNGs (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--start-section", type=int, default=None,
                         help="First book section number to render (see SECTION_PAGE_MAP)")
    parser.add_argument("--end-section", type=int, default=None,
                         help="Last book section number to render (inclusive)")
    parser.add_argument("--start-page", type=int, default=None,
                         help="First PDF page number to render, 1-indexed (overrides sections)")
    parser.add_argument("--end-page", type=int, default=None,
                         help="Last PDF page number to render, 1-indexed, inclusive")
    parser.add_argument("--scale", type=float, default=DEFAULT_SCALE,
                         help=f"Render zoom factor (default: {DEFAULT_SCALE}; "
                              f"use 6.0-10.0 for faded/small-print pages)")
    args = parser.parse_args()

    try:
        import pypdfium2 as pdfium
    except ImportError:
        sys.exit("Error: pypdfium2 is not installed for this Python.\n"
                  "Install it with: pip install pypdfium2\n"
                  "On this project's machine, D:\\python\\python.exe already has it.")

    source_path = Path(args.source)
    if not source_path.exists():
        sys.exit(f"Error: source PDF not found: {source_path}")

    start_page, end_page = resolve_page_range(args)
    if start_page < 1 or end_page < start_page:
        sys.exit(f"Error: invalid page range {start_page}-{end_page}.")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(str(source_path))
    total_pages = len(pdf)
    if end_page > total_pages:
        sys.exit(f"Error: end page {end_page} exceeds document length "
                  f"({total_pages} pages).")

    print(f"Source: {source_path}")
    print(f"Rendering PDF pages {start_page}-{end_page} "
          f"({end_page - start_page + 1} pages) at scale {args.scale} "
          f"into: {output_dir}")

    for page_num in range(start_page, end_page + 1):
        page = pdf[page_num - 1]  # pypdfium2 is 0-indexed
        bitmap = page.render(scale=args.scale)
        image = bitmap.to_pil()
        out_path = output_dir / f"page_{page_num:03d}.png"
        image.save(out_path)
        print(f"  wrote {out_path.name}  ({image.width}x{image.height})")

    print(f"Done. {end_page - start_page + 1} page(s) written to {output_dir}")


if __name__ == "__main__":
    main()
