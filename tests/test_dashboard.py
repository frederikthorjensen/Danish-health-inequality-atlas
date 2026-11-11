"""Read-only UI checks against the existing validated municipality outputs."""

import json
import unittest
import numpy as np
import pandas as pd

from streamlit.testing.v1 import AppTest

from src import dashboard_data as data
from src import dashboard_charts as charts


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (data.ROOT / "outputs/tables/analysis_manifest.json").exists():
            raise unittest.SkipTest("Create the validated analysis outputs first")
        cls.bundle = data.load_dashboard()

    def app(self):
        app = AppTest.from_file(str(data.ROOT / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        return app

    def test_every_page_smoke_and_saved_artifacts_unchanged(self):
        manifest_path = data.ROOT / "outputs/tables/analysis_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        before = {a["file"]: data.digest(data.ROOT / a["file"]) for a in manifest["artifacts"]}
        app = self.app()
        for page in ["key_findings", "comparison", "inequalities", "explanation", "explorer", "expected", "profiles", "methods", "data", "author"]:
            with self.subTest(page=page):
                app.switch_page(f"app_pages/{page}.py").run()
                self.assertFalse(app.exception)
                self.assertFalse(app.error)
        for filename, expected in before.items():
            self.assertEqual(expected, data.digest(data.ROOT / filename), filename)

    def test_home_headlines_match_validated_outputs(self):
        app = self.app()
        metrics = {m.label: m.value for m in app.metric}
        self.assertEqual(metrics["Municipality coverage"], "98")
        self.assertTrue(any("94 with published life expectancy" in c.value for c in app.caption))
        self.assertEqual(metrics["Strongest simple association"], "r = -0.814")
        self.assertEqual(metrics["Health behaviours"], "ΔR² = 0.062")
        self.assertEqual(metrics["Combined model"], "R² = 0.751")
        self.assertEqual(len(app.get("plotly_chart")), 0)

    def test_static_footer_contains_copyright_notice(self):
        app = self.app()
        footer = app.get_by_key("site_footer")
        text = "\n".join(item.value for item in footer.caption)
        self.assertIn("© 2026 Frederik Jensen", text)
        self.assertIn("Danish Health & Life Expectancy", text)
        app.switch_page("app_pages/author.py").run()
        self.assertFalse(app.exception)
        self.assertIn("© 2026 Frederik Jensen", "\n".join(item.value for item in app.get_by_key("site_footer").caption))

    def test_home_orientation_and_actions(self):
        app = self.app()
        text = "\n".join(item.value for item in app.markdown)
        for phrase in ["official Danish municipality-level", "descriptive and exploratory"]:
            self.assertIn(phrase,text)
        self.assertNotIn("Professional Bachelor of Physiotherapy", text)
        for key,title in [("home_explore","Health inequalities"),("home_report","Danish Health & Life Expectancy"),
            ("home_final_dashboard","Health inequalities"),("home_final_english","Danish Health & Life Expectancy"),
            ("home_final_danish","Sundhed og middellevetid i Danmark"),("home_final_methods","Methods & limitations")]:
            with self.subTest(action=key):
                current=self.app().button(key=key).click().run()
                self.assertFalse(current.exception)
                self.assertTrue(any(t.value==title for t in current.title))

    def test_author_has_dedicated_page_and_verified_qualifications(self):
        app = self.app().switch_page("app_pages/author.py").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "Frederik Jensen")
        text = "\n".join(item.value for item in [*app.markdown, *app.caption, *app.header, *app.subheader])
        for phrase in [
            "Professional Bachelor’s Degree in Physiotherapy",
            "Master of Science (MSc) in Critical Health Studies",
            "Roskilde University",
            "Narratives of Health Inequality",
            "Municipal Governance and Strategy for Youth Mental Health",
            "Factors Associated with Muscle Dysmorphia among Young Men",
            "Qualitative interviews · coding · document and discourse analysis",
            "No institutional or employer affiliation is claimed",
        ]:
            self.assertIn(phrase, text)
        self.assertTrue((data.ROOT / "assets/frederik_jensen_profile.png").exists())
        links = {item.value: item.url for item in app.get("link_button")}
        self.assertEqual(
            links["Connect on LinkedIn"],
            "https://www.linkedin.com/in/frederik-thor-jensen-887839111/",
        )
        self.assertEqual(len([item for item in app.expander if item.label == "Read the project description"]), 3)

    def test_author_page_is_visible_in_overview_navigation(self):
        app = self.app()
        visible_pages = [link.value for link in app.get_by_key("atlas_navigation").page_link]
        self.assertEqual(visible_pages[:3], ["Home", "Key findings", "About the author"])

    def test_key_findings_use_saved_values_and_explain_limits(self):
        app=self.app().switch_page("app_pages/key_findings.py").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value,"Key findings")
        self.assertEqual(len(app.subheader),7)
        evidence="\n".join(c.value for c in [*app.caption,*app.markdown])
        for value in ["-0.814","-0.810","+0.709","0.062","0.751","0.733"]:
            self.assertIn(value,evidence)
        text="\n".join(m.value for m in app.markdown)
        for caution in ["not establish an individual-level or causal effect","must not be interpreted as protective","not a single health-risk score"]:
            self.assertIn(caution,text)
        self.assertEqual(len(app.get("plotly_chart")),0)
        for topic,count in [("Social patterns",2),("Model insights",3),("Health profiles",1),("All findings",6)]:
            app.get_by_key("findings_topic").set_value(topic).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.subheader),count+1)

    def test_withheld_municipality_is_not_imputed(self):
        app = self.app().switch_page("app_pages/explorer.py").run()
        app.selectbox(key="municipality").select("Ærø").run()
        self.assertFalse(app.exception)
        self.assertEqual(sum(m.value == "Not published" for m in app.metric), 4)
        self.assertTrue(any("No estimate, prediction or residual" in item.value for item in app.info))
        app.switch_page("app_pages/expected.py").run()
        app.selectbox(key="prediction_highlight").select("Læsø").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("no fitted prediction or residual" in item.value for item in app.info))

    def test_interactive_selectors_and_downloads(self):
        app = self.app().switch_page("app_pages/inequalities.py").run()
        app.selectbox(key="inequality_variable").select("daily_smoking_pct").run()
        self.assertFalse(app.exception)
        app.switch_page("app_pages/explanation.py").run()
        app.get_by_key("correlation_method").set_value("Spearman").run()
        app.get_by_key("explanation_view").set_value("Adjusted models").run()
        app.get_by_key("coefficient_scale").set_value("Original units").run()
        self.assertFalse(app.exception)
        app.switch_page("app_pages/profiles.py").run()
        app.get_by_key("profiles_view").set_value("PCA explained").run()
        app.get_by_key("loading_component").set_value("PC2").run()
        app.get_by_key("profiles_view").set_value("Municipality profiles").run()
        app.selectbox(key="profile_highlight").select("Odder").run()
        self.assertFalse(app.exception)
        app.switch_page("app_pages/data.py").run()
        app.get_by_key("data_view").set_value("Sources & downloads").run()
        app.selectbox(key="download_table").select("All correlations and FDR results").run()
        self.assertFalse(app.exception)
        self.assertGreaterEqual(len(app.get("download_button")), 5)

    def test_report_sections_are_navigable_and_render_without_errors(self):
        app=self.app()
        sections=[
            ("inequalities","inequality_view",["Municipality comparison","Distribution"]),
            ("explanation","explanation_view",["Simple associations","Adjusted models"]),
            ("explorer","municipality_detail_view",["Health & behaviour","Social conditions","Model comparison"]),
            ("expected","expected_view",["Observed vs predicted","Municipality residuals","Model performance"]),
            ("profiles","profiles_view",["Municipality profiles","PCA explained","Choosing the profiles"]),
            ("methods","methods_view",["Limitations","Data sources","Statistical methods"]),
            ("data","data_view",["Municipality data","Data dictionary","Sources & downloads"]),
        ]
        for page,key,choices in sections:
            app.switch_page(f"app_pages/{page}.py").run()
            for choice in choices:
                with self.subTest(page=page,section=choice):
                    app.get_by_key(key).set_value(choice).run()
                    self.assertFalse(app.exception)
                    self.assertFalse(app.error)

    def test_scatter_line_matches_saved_pearson_result(self):
        # A display transform of the saved r, rather than fitting a new model.
        variable = "low_education_share_25_64_pct"
        x, y = data.association_line(self.bundle, variable)
        sample = self.bundle["master"][[variable, "life_expectancy_total"]].dropna()
        slope = (y[1]-y[0])/(x[1]-x[0])
        reconstructed = slope * sample[variable].std(ddof=1) / sample.life_expectancy_total.std(ddof=1)
        saved = data.characteristics(self.bundle).set_index("other_variable").loc[variable, "correlation"]
        self.assertAlmostEqual(reconstructed, saved, places=12)

    def test_descriptive_ranks_use_published_values_and_shared_ties(self):
        master=self.bundle["master"]
        for variable in ["life_expectancy_total","disposable_income_mean_dkk"]:
            decimals=0 if data.METRICS[variable][1]=="DKK" else 1
            series=master[variable].round(decimals)
            expected=series.rank(method="min",ascending=False)
            for index,row in master.iterrows():
                rank=data.descriptive_rank(master,variable,row[variable])
                if pd.isna(row[variable]):
                    self.assertIsNone(rank)
                else:
                    self.assertEqual(rank["rank"],int(expected.loc[index]))
                    self.assertEqual(rank["N"],int(series.count()))
        for rank,suffix in [(1,"1st"),(2,"2nd"),(3,"3rd"),(11,"11th"),(12,"12th"),(13,"13th"),(22,"22nd")]:
            self.assertIn(suffix,data.rank_label({"rank":rank,"N":98,"tied":False}))

    def test_chart_points_and_intervals_are_saved_results(self):
        b=self.bundle
        comparison=charts.model_comparison(b["fits"])
        np.testing.assert_allclose(comparison.data[0].y,b["fits"].adjusted_R_squared)
        coefficient=charts.coefficients(b["coefficients"],"Standardized beta")
        expected=b["coefficients"].loc[b["coefficients"].model.eq("M4") & b["coefficients"].term.ne("const")].iloc[::-1]
        np.testing.assert_allclose(coefficient.data[0].x,expected.standardized_beta)
        np.testing.assert_allclose(coefficient.data[0].error_x.array,expected.standardized_ci_high-expected.standardized_beta)
        predictions=b["predictions"].dropna(subset=["observed","predicted"])
        scatter=charts.prediction_scatter(b["predictions"],"Odder")
        np.testing.assert_allclose(scatter.data[0].x,predictions.predicted)
        np.testing.assert_allclose(scatter.data[0].y,predictions.observed)
        np.testing.assert_allclose(charts.scree(b["variance"]).data[0].y,b["variance"].explained_variance_ratio)
        np.testing.assert_allclose(charts.loading_chart(b["loadings"],"PC1").data[0].x,b["loadings"].PC1)
        pca=charts.pca_scatter(b["memberships"],None)
        for trace,(_,group) in zip(pca.data,b["memberships"].groupby("cluster"),strict=True):
            np.testing.assert_allclose(trace.x,group.PC1)
            np.testing.assert_allclose(trace.y,group.PC2)
        corr=data.characteristics(b).head(6)
        np.testing.assert_allclose(charts.correlation_bars(corr).data[0].x,corr.correlation)

    def test_municipality_hovers_have_names_and_readable_labels(self):
        b=self.bundle
        figures=[charts.association_scatter(b,"low_education_share_25_64_pct"),
            charts.prediction_scatter(b["predictions"],"Odder"),charts.pca_scatter(b["memberships"],"Odder"),
            charts.ranked(b["master"],"daily_smoking_pct","Lowest 20")]
        for fig in figures:
            for trace in fig.data:
                template=trace.hovertemplate or ""
                if trace.hoverinfo=="skip":
                    continue
                self.assertTrue(template)
                self.assertNotIn("life_expectancy_",template)
                self.assertNotIn("_pct",template)
                if trace.customdata is not None:
                    self.assertIn("customdata",template)
        self.assertNotEqual(charts.pca_scatter(b["memberships"],None).data[0].marker.symbol,
                            charts.pca_scatter(b["memberships"],None).data[1].marker.symbol)

    def test_charts_have_summary_findings_and_detailed_explanations(self):
        app = self.app()

        def assert_story(key):
            story = app.get_by_key(f"chart_story_{key}")
            text = "\n".join(item.value for item in story.markdown)
            self.assertIn("**What it shows**", text)
            self.assertIn("**Key finding**", text)
            self.assertIsNotNone(app.get_by_key(f"chart_detail_{key}"))

        for page, keys in [
            ("inequalities", ["inequality_ranked"]),
            ("explanation", ["association_bars", "correlation_heatmap", "association_scatter"]),
            ("explorer", ["municipality_profile"]),
            ("expected", ["prediction_scatter"]),
            ("profiles", ["cluster_pca", "cluster_profiles"]),
        ]:
            app.switch_page(f"app_pages/{page}.py").run()
            self.assertFalse(app.exception)
            for key in keys:
                assert_story(key)

        app.switch_page("app_pages/explanation.py").run()
        app.get_by_key("explanation_view").set_value("Adjusted models").run()
        for key in ["model_comparison", "model4_coefficients"]:
            assert_story(key)

        app.switch_page("app_pages/expected.py").run()
        app.get_by_key("expected_view").set_value("Municipality residuals").run()
        for key in ["residual_ranking", "residual_distribution"]:
            assert_story(key)

        app.switch_page("app_pages/profiles.py").run()
        app.get_by_key("profiles_view").set_value("PCA explained").run()
        for key in ["pca_scree", "pca_loadings"]:
            assert_story(key)
        app.get_by_key("profiles_view").set_value("Choosing the profiles").run()
        assert_story("cluster_selection")

    def test_text_palette_meets_normal_text_contrast(self):
        def luminance(colour):
            values=[int(colour[i:i+2],16)/255 for i in (1,3,5)]
            rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
            return sum(c*w for c,w in zip(rgb,[.2126,.7152,.0722],strict=True))
        for token in ["text","muted","accent","secondary"]:
            self.assertGreaterEqual((1.05)/(luminance(charts.TOKENS[token])+.05),4.5,token)
        high,low=sorted([luminance(charts.TOKENS["warning"]),luminance(charts.TOKENS["warning_surface"])],reverse=True)
        self.assertGreaterEqual((high+.05)/(low+.05),4.5)


if __name__ == "__main__":
    unittest.main()
