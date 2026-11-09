"""Publication integrity and separate-language reader checks; no inference reruns."""
import json
from pathlib import Path
import re
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.reporting import ROOT, REPORT, PDF_NAMES, load_results, report_context, sha
from src.report_views import publication


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,cls.tables=load_results()
        cls.sources={lang:(REPORT/f'final_report_{lang}.md').read_text() for lang in PDF_NAMES}

    def test_values_are_rendered_from_the_validated_snapshot(self):
        for lang in PDF_NAMES:
            context=report_context(lang,self.tables)
            template=(REPORT/'templates'/f'report_{lang}.md').read_text()
            expected=re.sub(r'\{\{(\w+)\}\}',lambda m:context[m[1]],template)
            self.assertEqual(expected,self.sources[lang])
            self.assertNotIn('{{',expected)
            for key,value in [('M1_r2','0.689'),('M2_r2','0.692'),('M3_r2','0.751'),('M4_r2','0.783'),
              ('M1_adj','0.682'),('M2_adj','0.678'),('M3_adj','0.733'),('M4_adj','0.762'),
              ('r_education','-0.814'),('r_smoking','-0.810'),('r_income','+0.709'),('delta_r2','0.062'),
              ('block_p','0.00097'),('loo_r2','0.706'),('pc1','60.4'),('pc2','17.8'),('silhouette','0.324'),('vif','9.56')]:
                self.assertEqual(context[key],value)

    def test_editions_have_identical_numerical_tables_and_figures(self):
        figures=[]
        tables=[]
        for lang,source in self.sources.items():
            self.assertEqual(len(source.split('<!-- page -->')),19)
            refs=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',source)
            self.assertEqual(len(refs),10)
            figures.append(refs)
            # Source description table has localized prose. All seven analytical tables share exact numbers.
            blocks=re.findall(r'(?:^\|.*\n)+',source,re.M)
            self.assertEqual(len(blocks),8)
            numeric=[]
            for table in blocks[1:]:
                rows=[]
                for line in table.splitlines()[2:]:
                    cells=[v.strip() for v in line.strip('|').split('|')[1:]]
                    rows.append([v for v in cells if re.fullmatch(r'[+\-\d.e; –]+',v)])
                numeric.append(rows)
            tables.append(numeric)
            for i in range(1,11):
                word='Figure' if lang=='en' else 'Figur'
                self.assertEqual(len(re.findall(rf'\*\*{word} {i}\.',source)),1)
                self.assertGreaterEqual(len(re.findall(rf'(?:{word}|{word.lower()}) {i}\b',source)),2)
            for i in range(1,9):
                word='Table' if lang=='en' else 'Tabel'
                self.assertEqual(len(re.findall(rf'\*\*{word} {i}\.',source)),1)
            for name in ['Ærø','Fanø','Samsø','Læsø']:
                self.assertIn(name,source)
        self.assertEqual(figures[0],figures[1])
        self.assertEqual(tables[0],tables[1])

    def test_prose_headlines_match_saved_details(self):
        load=self.tables['pca_loadings'].set_index('variable')
        for term,value in [('less_good_or_poor_self_rated_health_pct',.912),('obesity_pct',.908),
             ('physical_inactivity_pct',.887),('daily_smoking_pct',.855),('poor_mental_health_pct',.443),('risky_alcohol_pct',-.501)]:
            self.assertAlmostEqual(round(load.loc[term,'PC1'],3),value)
        self.assertEqual(self.tables['cluster_sizes'].N.tolist(),[34,64])
        diag=self.tables['model_diagnostics'].set_index('model')
        self.assertEqual(int(diag.loc['M4','high_Cook_N']),7)
        self.assertEqual(int(diag.loc['M3','high_Cook_N']),6)
        secondary=self.tables['secondary_regression_coefficients']
        retained=secondary.loc[secondary.q_value_family_BH.lt(.05)].groupby('outcome').term.apply(set).to_dict()
        self.assertEqual(retained['life_expectancy_male'],{'income_per_10000_dkk','low_education_share_25_64_pct','daily_smoking_pct','obesity_pct'})
        self.assertEqual(retained['life_expectancy_female'],{'income_per_10000_dkk','daily_smoking_pct'})
        self.assertNotIn('life_expectancy_sex_gap',retained)
        withheld=set(self.tables['master'].loc[self.tables['master'].life_expectancy_total.isna(),'municipality'])
        self.assertEqual(withheld,{'Ærø','Fanø','Samsø','Læsø'})
        residual=self.tables['municipality_predictions_residuals'].dropna(subset=['residual'])
        self.assertEqual(residual.nlargest(5,'residual').municipality.tolist(),['Odder','Vallensbæk','Varde','Lejre','Kerteminde'])
        self.assertEqual(residual.nsmallest(5,'residual').municipality.tolist(),['København','Guldborgsund','Herlev','Aalborg','Brønderslev'])

    def test_publication_delivery_checksums_and_pdf_contents(self):
        metadata=json.loads((REPORT/'publication_manifest.json').read_text())
        self.assertEqual(sha(ROOT/'outputs/tables/analysis_manifest.json'),metadata['analysis_manifest_sha256'])
        for file,checksum in metadata['figure_sources'].items():
            self.assertEqual(sha((REPORT/file).resolve()),checksum)
        try:
            from pypdf import PdfReader
        except ImportError:
            self.skipTest('Install requirements-report.txt for PDF text/pagination checks')
        for lang in PDF_NAMES:
            record,payload,sections,_=publication(lang)
            self.assertEqual(payload,(ROOT/PDF_NAMES[lang]).read_bytes())
            pdf=PdfReader(ROOT/PDF_NAMES[lang])
            self.assertEqual(len(pdf.pages),record['pages'])
            self.assertEqual(len(pdf.pages),len(sections))
            text='\n'.join(p.extract_text() for p in pdf.pages)
            for term in ['Frederik Jensen','0.751','0.706','0.324','0.00097','81.6']:
                self.assertIn(term,text)
            self.assertEqual(len(re.findall(r'(?:Figure|Figur) \d+\.',text)),10)

    def test_report_navigation_and_separate_readers(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        app.switch_page('app_pages/report.py').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get('download_button')),2)
        for lang in PDF_NAMES:
            app.switch_page(f'app_pages/report_{lang}.py').run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.get('download_button')),1)
            self.assertEqual(app.selectbox(key=f'report_section_{lang}').value,0)
            app.button(key=f'report_next_{lang}').click().run()
            self.assertEqual(app.selectbox(key=f'report_section_{lang}').value,1)
            for index in range(len(publication(lang)[2])):
                app.selectbox(key=f'report_section_{lang}').select(index).run()
                self.assertFalse(app.exception)
                self.assertFalse(app.error)
            app.switch_page('app_pages/report.py').run()
            self.assertFalse(app.exception)
