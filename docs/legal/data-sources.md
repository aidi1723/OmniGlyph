# Data Sources and License Notes

OmniGlyph separates project source code licensing from imported data licensing.

## Project Code

- License: Apache License 2.0, defined in `LICENSE`.
- Scope: OmniGlyph source code, tests, scripts, and documentation written for this repository.

## Imported Data Policy

Imported data is not relicensed by OmniGlyph. Every source snapshot must preserve:

- source name
- source URL
- source version or release tag
- retrieval timestamp
- SHA-256 checksum
- license or terms note
- local path

Canonical facts must point back to a `source_snapshot` row.

## Initial Source Classes

### Unicode Character Database

- Purpose: Unicode code point, character name, category, and related standard properties.
- Default URL: `https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt`
- License/terms: Unicode Terms of Use. Operators must review Unicode terms before redistribution.
- Current implementation: `omniglyph download-unicode` and `omniglyph ingest-unicode --source ...`.

### Unihan Database

- Purpose: CJK readings, definitions, variants, stroke counts, and dictionary-style properties.
- Typical source artifact: `Unihan.zip` from Unicode UCD release directories.
- License/terms: Unicode Terms of Use. Operators must review Unicode terms before redistribution.
- Current implementation: `omniglyph ingest-unihan --source ...` accepts tab-separated Unihan text files such as `Unihan_Readings.txt`.

### CLDR

- Purpose: locale display names, script names, emoji annotations, and multilingual labels.
- Status: planned, not implemented in v0.2.0-beta.
- License/terms: CLDR/Unicode terms must be reviewed before ingestion.

### Private Domain Packs

- Purpose: private business vocabulary such as architectural profiles, glass specifications, HS codes, logistics terms, and trade abbreviations.
- Status: namespace-supported through `private_*` properties; access control is not implemented in v0.2.0-beta.
- Requirement: private terms must not overwrite global Unicode, Unihan, or CLDR facts.

## Redistribution Warning

Do not publish bundled upstream data artifacts unless their license permits redistribution and attribution requirements are satisfied. The repository should publish ingestion code and small synthetic fixtures by default, not full upstream datasets.
