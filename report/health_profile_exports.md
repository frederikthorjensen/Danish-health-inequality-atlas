# Reproduce the official municipality exports

Automated acquisition succeeded on 6 November 2026: **2025, six reports, 98 municipalities per report**. No manual export is currently required. Use the original raw snapshot to reproduce processing offline.

## Automated acquisition and offline import

```bash
source .venv/bin/activate
python -m pip install -r requirements-health.txt
python -m playwright install chromium
python -m src.health_profile_collection --wave 2025
python -m src.health_profile_import --raw-dir data/raw/health_profile_2025_20261106T120114Z_5041ba1d
```

Use the new snapshot directory printed by the collection command when refreshing. Playwright is an optional acquisition dependency; the importer uses the existing pandas/openpyxl dependencies. Chromium and Playwright used during this investigation were installed temporarily under `/private/tmp`, so install them with the commands above for an independent repeat run. Acquisitions create exclusive raw directories; importing does not modify raw or the socioeconomic master. A failed refresh cannot silently replace the wave or become a successful snapshot. `--wave 2021` is an explicit fallback if 2025 later becomes unavailable; do not mix waves across the six reports.

The raw XLSX exports do not themselves label their selected year in the table header. The acquisition manifest records the verified selected radio control and all export selections. Keep the manifest and official definition HTML with the workbooks. Do not relabel the files as another wave.

## Manual fallback selections (only if automation later stops working)

These controls were verified in the public guest viewer. Start at [Danskernes Sundhed](https://www.danskernessundhed.dk/). Allow normal site cookies. If a login page appears, use only its public **Guest** option when offered; if guest access fails, stop rather than entering or guessing credentials.

For each indicator below:

1. Open its menu item, then the **Beskrivelse af indikatoren** tab. Save that definition with the export; it documents the measure and selected response categories.
2. Select **Kommune**. Select **2025**. Leave every region box unchecked and leave the municipality dropdown unfiltered to include all municipalities. Use the report's combined-sex municipality prevalence; do not choose an age, education, or sex subgroup, a trend tab, or an OR map.
3. Right-click inside the municipality table and choose **Export data...** (the object menu provides the same command).
4. In the export dialog, enter **1-98** under Rows. Keep all columns selected, including **Kommune** and the prevalence column. Keep **Formatted data** checked. Select **Excel workbook (*.xlsx)** and click **OK**. Keep the workbook unchanged; preserve the suppression/blank cells.
5. Save the source URL, selected wave, filters, and retrieval date alongside each original file. A manual file must not be relabelled as an automated snapshot. The `import_workbook(path, indicator_key, registry)` function in `src/health_profile_import.py` reads this exact XLSX export format; a full snapshot additionally requires the provenance manifest and definition checks used by `import_snapshot`.

| Pipeline key / filename | Portal menu item | Prevalence column (export this; accompanying OR is separate) |
| --- | --- | --- |
| `daily_smoking_2025.xlsx` | Sundhedsadfærd → Tobaks- og nikotinprodukter → Daglig rygning | Andel der ryger dagligt |
| `obesity_2025.xlsx` | Sundhedsadfærd → Overvægt og undervægt → Svær overvægt | Andel med svær overvægt |
| `physical_inactivity_2025.xlsx` | Sundhedsadfærd → Fysisk aktivitet → Opfylder ikke WHO’s minimumsanbefaling for fysisk aktivitet | Andel der ikke opfylder WHO’s minimums anbefaling for fysisk aktivitet |
| `risky_alcohol_2025.xlsx` | Sundhedsadfærd → Alkoholforbrug → Drikker mere end 10 genstande på en typisk uge | Andel der drikker mere end 10 genstande i løbet af en typisk uge |
| `good_self_rated_health_2025.xlsx` | Helbred og trivsel → Helbredsrelateret livskvalitet → Selvvurderet helbred | Andel med fremragende, vældig godt eller godt selvvurderet helbred |
| `poor_mental_health_2025.xlsx` | Helbred og trivsel → Helbredsrelateret livskvalitet → Mentalt helbred | Andel med lav score på den mentale helbredsskala |

Choose **2021 for all six** only if 2025 is not available at municipality level, and record that fallback explicitly. No fallback was needed in the completed snapshot. High mental well-being is a separate construct and is not used to manufacture a low-well-being indicator. Self-rated health is imported as good health and then complemented only after verifying the five-category partition; the resulting label means less good or poor, not poor alone.

Official export documentation: [portal guide](https://www.danskernessundhed.dk/Vejledning.html), [FAQ](https://www.danskernessundhed.dk/FAQ.html), and [SAS Viewer 7.5 manual](https://documentation.sas.com/api/docsets/vavwr/7.5/content/vavwr.pdf?locale=en). The browser's export dialog was inspected directly; its live labels take precedence if translated.
