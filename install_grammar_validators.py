#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_grammar_validators.py
==============================
One-time setup script: installs the three Sanskrit grammar-validation
libraries found for this project, using YOUR OWN python.exe/pip (the
one this script is run with) -- run this once:

    D:\\python\\python.exe install_grammar_validators.py

Installs:
  sanskrit_parser  -- kmadathil/sanskrit_parser: sandhi split, morphological
                       tagging, and full vakya (sentence) parse. Good for
                       cross-checking samasa_splitter.py's compound splits.
                       https://github.com/kmadathil/sanskrit_parser
  vidyut           -- ambuda-org/vidyut: Rust-based toolkit (Python bindings)
                       with vidyut-prakriya (2000+ Ashtadhyayi rules, word
                       generation with full derivation trace), vidyut-cheda
                       (segmentation+morphology), vidyut-kosha (dictionary),
                       vidyut-chandas (meter ID), vidyut-lipi (transliteration).
                       https://github.com/ambuda-org/vidyut
                       NOTE: the maintainers' own 2026 release notes say
                       vidyut.cheda has regressed and now recommend the
                       Dharmamitra tools (https://github.com/dharmamitra)
                       for segmentation specifically -- vidyut-prakriya/
                       kosha/chandas/lipi are still actively maintained.
  chanda           -- hrishikeshrt/chanda (Chandojnanam): 200+ Sanskrit
                       meters, exact + fuzzy meter identification, multi-
                       script input. This directly automates Component 10
                       (chandas) instead of needing MANUAL_DATA for every
                       verse -- see chandas_helper.py in this folder.
                       https://github.com/hrishikeshrt/chanda

This script only installs packages; it does not modify any project file.
"""
import subprocess
import sys

PACKAGES = ["sanskrit_parser", "vidyut", "chanda"]

def main():
    print(f"Using: {sys.executable}")
    failed = []
    for pkg in PACKAGES:
        print(f"\n--- installing {pkg} ---")
        rc = subprocess.call([sys.executable, "-m", "pip", "install", "--upgrade", pkg])
        if rc != 0:
            failed.append(pkg)
    print("\n=== done ===")
    if failed:
        print(f"Failed to install: {', '.join(failed)}")
        print("If pip reports 'Access is denied', re-run from an elevated "
              "prompt, or check that this python.exe's Lib\\site-packages "
              "folder is writable by your user account.")
        sys.exit(1)
    print("All three installed successfully. Quick self-test:")
    try:
        import chanda
        print("  chanda: OK (import chanda.analyze_text)")
    except Exception as e:
        print(f"  chanda: import failed -- {e}")
    try:
        import sanskrit_parser
        print("  sanskrit_parser: OK")
    except Exception as e:
        print(f"  sanskrit_parser: import failed -- {e}")
    try:
        import vidyut
        print("  vidyut: OK (note: needs a separate data download to be useful -- "
              "see https://github.com/ambuda-org/vidyut-py for the data-*.zip link)")
    except Exception as e:
        print(f"  vidyut: import failed -- {e}")


if __name__ == "__main__":
    main()
