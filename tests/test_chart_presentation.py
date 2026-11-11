"""Presentation changes must preserve published values, uncertainty and missingness."""
import unittest
import numpy as np
from src import dashboard_charts as charts
from src.dashboard_data import load_dashboard, characteristics, METRICS, FEATURES
from src.dashboard_comparison import comparison_table, comparison_figure


class PresentationIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=load_dashboard()

    def test_ranked_views_keep_every_published_value_and_tie(self):
        for variable in METRICS:
            source=self.b['master'].dropna(subset=[variable]).sort_values(variable,kind='stable')
            for selection,expected in [('Lowest 20',source.head(20)),('Highest 20',source.tail(20)),('All published',source)]:
                with self.subTest(variable=variable,view=selection):
                    fig=charts.ranked(self.b['master'],variable,selection)
                    np.testing.assert_array_equal(fig.data[0].x,expected[variable])
                    self.assertEqual(list(fig.data[0].y),expected.municipality.tolist())
                    median=float(source[variable].median())
                    self.assertEqual(fig.layout.shapes[0].x0,median)

    def test_both_correlation_methods_preserve_exact_saved_statistics(self):
        for method in ['Pearson','Spearman']:
            source=characteristics(self.b,method)
            fig=charts.correlation_bars(source,limit=len(source))
            np.testing.assert_allclose(fig.data[0].x,source.correlation)
            np.testing.assert_allclose(np.asarray(fig.data[0].customdata,dtype=float),source[['N','p_value','q_value_BH_all_pairs']])
            self.assertEqual(fig.layout.xaxis.range[0],-fig.layout.xaxis.range[1])
            for label,variable in zip(fig.data[0].y,source.other_variable,strict=True):
                self.assertEqual(label.replace('<br>',' '),charts.LABELS[variable])

    def test_both_forest_scales_keep_saved_estimates_and_hc3_intervals(self):
        source=self.b['coefficients'].loc[lambda d:d.model.eq('M4') & d.term.ne('const')].iloc[::-1]
        for mode,estimate,low,high in [('Standardized beta','standardized_beta','standardized_ci_low','standardized_ci_high'),('Original units','coefficient','ci_low','ci_high')]:
            trace=charts.coefficients(self.b['coefficients'],mode).data[0]
            np.testing.assert_allclose(trace.x,source[estimate])
            np.testing.assert_allclose(trace.error_x.array,source[high]-source[estimate])
            np.testing.assert_allclose(trace.error_x.arrayminus,source[estimate]-source[low])

    def test_profiles_keep_saved_scaling_and_original_alcohol_direction(self):
        row=self.b['master'].set_index('municipality').loc['Odder']
        scaling=self.b['scaling'].set_index('variable')
        source=(row[scaling.index].astype(float)-scaling['mean'])/scaling.SD_ddof0
        np.testing.assert_allclose(charts.explorer_profile(self.b,row).data[0].x,source)
        profiles=self.b['profiles'].set_index('cluster')
        fig=charts.cluster_comparison(profiles,FEATURES)
        for trace,(_,profile) in zip(fig.data,profiles.iterrows(),strict=True):
            np.testing.assert_allclose(trace.x,profile[FEATURES])
        self.assertGreater(profiles.loc[1,'risky_alcohol_pct'],0)
        self.assertLess(profiles.loc[1,'daily_smoking_pct'],0)

    def test_residuals_keep_largest_absolute_saved_values(self):
        source=self.b['predictions'].dropna(subset=['residual'])
        expected=source.loc[source.residual.abs().sort_values(ascending=False,kind='stable').head(16).index]
        trace=charts.residual_ranking(self.b['predictions']).data[0]
        np.testing.assert_allclose(trace.x,expected.residual)
        self.assertEqual(list(trace.y),expected.municipality.tolist())

    def test_two_to_four_places_and_equal_values_keep_original_units(self):
        for names in [['København','Aarhus'],['København','Aarhus','Odder'],['København','Aarhus','Odder','Aalborg']]:
            table=comparison_table(self.b['master'],names,list(METRICS),names[-1])
            for variable in METRICS:
                fig=comparison_figure(table,variable)
                points=[trace for trace in fig.data if trace.mode in ['markers','markers+text']]
                expected=table.loc[table.variable.eq(variable)]
                self.assertEqual(len(points),len(names))
                for trace,row in zip(points,expected.itertuples(),strict=True):
                    self.assertEqual(trace.x[0],row.value)
                    self.assertEqual(trace.customdata[0][1],names[-1])
        # A tied dumbbell is still two observations, not a fabricated difference.
        table=comparison_table(self.b['master'],['København','Aarhus'],['daily_smoking_pct'],'København')
        table['value']=10.0; table['reference_value']=10.0; table['difference']=0.0
        fig=comparison_figure(table,'daily_smoking_pct')
        self.assertEqual([t.x[0] for t in fig.data[:2]],[10.,10.])
        self.assertLess(fig.layout.xaxis.range[0],10.)
        self.assertGreater(fig.layout.xaxis.range[1],10.)
