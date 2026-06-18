from pathlib import Path


ROOT = Path(__file__).parent


def test_weekly_workflow_exports_and_publishes_report():
    workflow = (ROOT / ".github" / "workflows" / "weekly-crawl.yml").read_text()

    assert "export_to_html" in workflow
    assert "reports/" in workflow
    assert "git push origin main" in workflow


def test_deploy_script_uses_standalone_crawl_job():
    deploy_script = (ROOT / "deploy.sh").read_text()

    assert "python3 scripts/crawl_job.py" in deploy_script
    assert "backend/main.py --trigger" not in deploy_script
