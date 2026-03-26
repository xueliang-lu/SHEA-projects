# Debugging Agent TODO (from QA)

1. **Implement missing project modules for test contracts**
   - Create `cpl_automation.parser` with `parse_transcript(text)`.
   - Create `cpl_automation.matcher` with `match_courses(extraction, catalog)`.
   - Create `cpl_automation.db` with `CPLRepository` and CRUD methods used by tests.
   - Create `cpl_automation.export` with `export_applications_to_csv(rows, output_path)`.

2. **Align implementation output schema to fixtures**
   - Ensure parser outputs keys required by tests.
   - Normalize `decision` values to `approved|partial|rejected`.

3. **Build decision-audit persistence model**
   - Include rationale/update history for manual overrides.
   - Confirm DB methods return dictionary-like rows compatible with tests.

4. **Match CSV headers with reporting requirements**
   - Include stable field ordering in export.
   - Ensure UTF-8 newline-safe writing for cross-platform reads.

5. **Close QA gap: extraction accuracy harness metric**
   - Add benchmark runner that reports exact-match and overlap rates over fixture set.
