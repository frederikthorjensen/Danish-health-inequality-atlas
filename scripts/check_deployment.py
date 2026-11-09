"""Offline release verification: python -m scripts.check_deployment."""
from pathlib import Path
import json

from src.dashboard_data import load_dashboard
from src.reporting import load_results,PDF_NAMES,ROOT
from src.report_views import publication


def main():
    bundle=load_dashboard();load_results()
    assert len(bundle['master'])==98
    assert bundle['master'].life_expectancy_total.count()==94
    for lang,file in PDF_NAMES.items():
        record,pdf,sections,_=publication(lang)
        assert pdf.startswith(b'%PDF-')
        assert record['pages']==len(sections)
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    if app.exception:raise RuntimeError(str(app.exception))
    pages=sorted((ROOT/'app_pages').glob('*.py'))
    for page in pages:
        app.switch_page('app_pages/'+page.name).run()
        if app.exception or app.error:raise RuntimeError(f'Page failed: {page.name}')
    print(f'Validated 98 municipalities, 94 published outcomes, both PDFs and all {len(pages)} pages.')
    print('No source API calls, browser downloads or analytical refits were needed.')


if __name__=='__main__':main()
