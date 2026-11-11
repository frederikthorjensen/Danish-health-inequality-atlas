"""Direct comparison must preserve original observations, units and missing values."""
import unittest
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from src.dashboard_data import ROOT,load_dashboard,METRICS
from src.dashboard_comparison import PRESETS,comparison_table,comparison_figure,difference_text


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.master=load_dashboard()['master']

    def app(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run().switch_page('app_pages/comparison.py').run()
        self.assertFalse(app.exception)
        return app

    def test_values_and_differences_match_original_units(self):
        names=['København','Aarhus','Odder','Aalborg']
        original=self.master.set_index('municipality')
        for reference in names:
            table=comparison_table(self.master,names,list(METRICS),reference)
            for row in table.itertuples():
                self.assertEqual(row.value,original.loc[row.municipality,row.variable])
                self.assertAlmostEqual(row.difference,row.value-original.loc[reference,row.variable],places=10)
                self.assertEqual(row.period,METRICS[row.variable][2])
                self.assertEqual(row.difference_unit,'pp' if row.unit=='%' else row.unit)
        self.assertEqual(difference_text(1.2,'daily_smoking_pct'),'+1.2 pp')
        self.assertEqual(difference_text(10000,'disposable_income_mean_dkk'),'+10,000 DKK')

    def test_withheld_reference_is_never_imputed(self):
        table=comparison_table(self.master,['Ærø','København'],['life_expectancy_total','daily_smoking_pct'],'Ærø')
        life=table.loc[table.variable.eq('life_expectancy_total')]
        self.assertTrue(life.difference.isna().all())
        self.assertTrue(life.reference_value.isna().all())
        self.assertTrue(pd.isna(life.loc[life.municipality.eq('Ærø'),'value'].iloc[0]))
        self.assertEqual(len(comparison_figure(table,'life_expectancy_total').data),1)
        missing=comparison_table(self.master,['Ærø','Fanø'],['life_expectancy_total'],'Ærø')
        figure=comparison_figure(missing,'life_expectancy_total')
        self.assertEqual(len(figure.data),0)
        self.assertEqual(sum('Not published' in a.text for a in figure.layout.annotations),2)
        self.assertIn('Difference unavailable',difference_text(np.nan,'life_expectancy_total'))

    def test_charts_show_published_points_and_human_tooltips(self):
        table=comparison_table(self.master,['København','Aarhus'],['daily_smoking_pct'],'København')
        figure=comparison_figure(table,'daily_smoking_pct')
        for trace,row in zip([t for t in figure.data if t.mode=="markers"],table.itertuples(),strict=True):
            self.assertEqual(trace.x[0],row.value)
            self.assertEqual(trace.y[0],0)
            self.assertIn(row.municipality,trace.hovertemplate)
            self.assertIn('Daily smoking',trace.hovertemplate)
            self.assertNotIn('_pct',trace.hovertemplate)
        self.assertNotEqual(figure.data[0].marker.symbol,figure.data[1].marker.symbol)

    def test_ui_presets_reference_changes_and_empty_states(self):
        app=self.app()
        app.multiselect(key='comparison_municipalities').set_value(['Ærø','København','Aarhus']).run()
        app.selectbox(key='comparison_reference').select('Ærø').run()
        self.assertFalse(app.exception)
        self.assertTrue(any('not published' in item.value for item in app.info))
        app.get_by_key('comparison_preset').set_value('Health & behaviour').run()
        self.assertEqual(len(app.multiselect(key='comparison_factors').value),6)
        self.assertFalse(app.exception)
        app.get_by_key('comparison_display').set_value('Table').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe),1)
        app.multiselect(key='comparison_municipalities').set_value(['Aarhus','Odder']).run()
        self.assertIn(app.selectbox(key='comparison_reference').value,['Aarhus','Odder'])
        app.multiselect(key='comparison_factors').set_value([]).run()
        self.assertTrue(any('at least one indicator' in item.value for item in app.info))
        app.multiselect(key='comparison_municipalities').set_value([]).run()
        self.assertFalse(app.exception)
        self.assertTrue(any('at least two municipalities' in item.value for item in app.info))

    def test_comparison_charts_have_explanations(self):
        app=self.app()
        self.assertFalse(app.exception)
        for variable in PRESETS["Key indicators"]:
            story=app.get_by_key(f"chart_story_comparison_{variable}")
            text="\n".join(item.value for item in story.markdown)
            self.assertIn("**What it shows**",text)
            self.assertIn("**What to notice:**",text)
            self.assertIsNotNone(app.get_by_key(f"chart_detail_comparison_{variable}"))

    def test_explorer_handoff_preserves_the_selected_municipality(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run().switch_page('app_pages/explorer.py').run()
        app.selectbox(key='municipality').select('Odder').run()
        app.button(key='open_municipality_comparison').click().run()
        self.assertFalse(app.exception)
        self.assertIn('Odder',app.multiselect(key='comparison_municipalities').value)
