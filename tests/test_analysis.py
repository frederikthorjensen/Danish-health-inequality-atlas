"""Numerical validation against real data; no synthetic health observations."""

from pathlib import Path
import unittest

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import analysis


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = analysis.ROOT / "data/processed/municipality_master.csv"
        if not path.exists():
            raise unittest.SkipTest("Acquire the official final municipality master first")
        cls.data = analysis.load_data(path)

    def test_expected_sample_sizes_and_excluded_municipalities(self):
        self.assertEqual(len(self.data), 98)
        for outcome in analysis.OUTCOMES:
            sample = analysis.complete_cases(self.data, outcome, analysis.MODELS["M4"])
            self.assertEqual(len(sample), 94)
            self.assertTrue({"492", "563", "741", "825"}.isdisjoint(sample.municipality_code))
        self.assertEqual(len(analysis.prepare_health_features(self.data)[0]), 98)

    def test_new_predictor_missingness_excludes_without_imputation(self):
        damaged = self.data.copy()
        i = damaged.life_expectancy_total.first_valid_index()
        code = damaged.loc[i, "municipality_code"]
        damaged.loc[i, "daily_smoking_pct"] = np.nan
        sample = analysis.complete_cases(damaged, "life_expectancy_total", analysis.MODELS["M3"])
        self.assertEqual(len(sample), 93)
        self.assertNotIn(code, set(sample.municipality_code))
        self.assertTrue(pd.isna(damaged.loc[i, "daily_smoking_pct"]))

    def test_standardized_coefficients_match_independent_standardized_fit(self):
        result, sample, table, _, _ = analysis.fit_model(self.data, "life_expectancy_total", analysis.MODELS["M4"], "M4")
        x, y = sample[analysis.MODELS["M4"]], sample.life_expectancy_total
        standardized = sm.OLS((y - y.mean()) / y.std(ddof=1),
            sm.add_constant((x - x.mean()) / x.std(ddof=1)), missing="raise").fit(cov_type="HC3", use_t=True)
        table = table.set_index("term")
        for term in x:
            self.assertAlmostEqual(table.loc[term, "standardized_beta"], standardized.params[term], places=10)
            self.assertAlmostEqual(analysis.standardized_beta(result.params[term], x[term], y), standardized.params[term], places=10)
            np.testing.assert_allclose(table.loc[term, ["standardized_ci_low", "standardized_ci_high"]].astype(float), standardized.conf_int().loc[term], atol=1e-10)
        self.assertEqual(result.cov_type, "HC3")
        self.assertTrue(result.use_t)

    def test_residual_identity_and_no_withheld_predictions(self):
        result, sample, _, _, _ = analysis.fit_model(self.data, "life_expectancy_total", analysis.MODELS["M3"], "M3")
        table = analysis.residual_table(self.data, result, sample)
        observed = table.dropna(subset=["observed"])
        np.testing.assert_allclose(observed.residual, observed.observed - observed.predicted, atol=1e-12)
        excluded = table.loc[table.municipality_code.isin(["492", "563", "741", "825"])]
        self.assertEqual(len(excluded), 4)
        self.assertTrue(excluded[["observed", "predicted", "residual", "loo_predicted"]].isna().all().all())

    def test_leave_one_out_press_matches_refitting(self):
        result, sample, _, _, _ = analysis.fit_model(self.data, "life_expectancy_total", analysis.MODELS["M3"], "M3")
        predictions = analysis.residual_table(self.data, result, sample).set_index("municipality_code")
        for index in [sample.index[0], sample.index[len(sample)//2], sample.index[-1]]:
            other = sample.drop(index=index)
            refit, _, _, _, _ = analysis.fit_model(other, "life_expectancy_total", analysis.MODELS["M3"], "loo")
            x = sm.add_constant(sample.loc[[index], analysis.MODELS["M3"]], has_constant="add")
            actual = float(refit.predict(x).iloc[0])
            self.assertAlmostEqual(actual, predictions.loc[sample.loc[index, "municipality_code"], "loo_predicted"], places=9)

    def test_pca_input_directionality_and_standardization(self):
        sample, scaled, _ = analysis.prepare_health_features(self.data)
        np.testing.assert_allclose(scaled.mean(axis=0), 0, atol=1e-12)
        np.testing.assert_allclose(scaled.std(axis=0, ddof=0), 1, atol=1e-12)
        for i, variable in enumerate(analysis.HEALTH_FEATURES):
            self.assertEqual(analysis.FEATURE_DIRECTIONS[variable], 1)
            self.assertGreater(np.corrcoef(sample[variable], scaled[:, i])[0, 1], .999999999)
            np.testing.assert_array_equal(np.argsort(sample[variable].to_numpy()), np.argsort(scaled[:, i]))

    def test_all_correlation_pairs_and_declared_fdr_families_saved(self):
        table = analysis.correlations(self.data)
        self.assertEqual(len(table), 2 * 136)
        self.assertEqual(table.groupby("method").size().to_dict(), {"Pearson": 136, "Spearman": 136})
        self.assertTrue(table.q_value_BH_all_pairs.between(0, 1).all())
        self.assertEqual(table.q_value_BH_total_life_expectancy_family.notna().sum(), 32)
        self.assertTrue((table.q_value_BH_all_pairs + 1e-14 >= table.p_value).all())


if __name__ == "__main__":
    unittest.main()
