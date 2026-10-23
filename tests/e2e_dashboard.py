"""Optional browser end-to-end test of the dashboard.
Needs: pip install playwright && playwright install chromium
Run from the repo root: python tests/e2e_dashboard.py"""
import os, subprocess, sys, time, tempfile, json
from playwright.sync_api import sync_playwright
port = 3555
env = {**os.environ, "PORT": str(port), "PANTRY_DB": os.path.join(tempfile.mkdtemp(), "s.json")}
srv = subprocess.Popen([sys.executable, "-m", "pantrypilot"], env=env, stdout=subprocess.DEVNULL)
time.sleep(1.2)
results = []
def check(name, cond, extra=""):
    results.append((name, bool(cond))); print(("PASS " if cond else "FAIL ") + name, extra)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width":1280,"height":900})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"http://localhost:{port}/"); pg.wait_for_timeout(800)
        check("loads + connects", "Connected" in pg.inner_text("#message"), pg.inner_text("#message"))
        # preferences saved first (so we can test they reload)
        pg.select_option("#diet", "vegetarian"); pg.fill("#dislikes", "mushroom")
        pg.click("#preference-form button[type=submit]"); pg.wait_for_timeout(500)
        # add item
        pg.fill("#item-name", "Tomato"); pg.fill("#item-quantity", "6")
        from datetime import date, timedelta
        pg.fill("#item-expiry", (date.today()+timedelta(days=1)).isoformat())
        pg.click("#add-item-form button[type=submit]"); pg.wait_for_timeout(700)
        msg = pg.inner_text("#message")
        check("add item shows success (not error)", "added to your pantry" in msg, msg)
        check("pantry list updated", "tomato" in pg.inner_text("#pantry-list").lower())
        check("form cleared", pg.input_value("#item-name") == "")
        check("expiry auto-checked", pg.inner_text("#expiry-count") == "1", pg.inner_text("#expiry-count"))
        pg.reload(); pg.wait_for_timeout(800)
        check("diet persists after reload (stat)", pg.inner_text("#diet-value").lower() == "vegetarian", pg.inner_text("#diet-value"))
        check("diet persists after reload (dropdown)", pg.input_value("#diet") == "vegetarian")
        check("dislikes persist after reload", pg.input_value("#dislikes") == "mushroom")
        pg.click("#suggest-meals"); pg.wait_for_timeout(700)
        check("meals shown", pg.locator(".meal-card").count() > 0, pg.locator(".meal-card").count())
        pg.click("#build-shopping-list"); pg.wait_for_timeout(700)
        sl = pg.inner_text("#shopping-list")
        check("shopping list without picking a meal is NOT empty", "everything" not in sl.lower() and "no shopping" not in sl.lower() and len(sl) > 5, sl[:80].replace("\n"," | "))
        pg.screenshot(path="/tmp/dash.png", full_page=True)
        # use item (cancel prompt => silent)
        pg.once("dialog", lambda d: d.dismiss())
        pg.click("#pantry-list .item-row button"); pg.wait_for_timeout(400)
        check("cancel prompt is silent", "valid positive" not in pg.inner_text("#message"), pg.inner_text("#message"))
        check("no JS page errors", not errs, errs)
        b.close()
finally:
    srv.terminate()
print(f"\n{sum(ok for _,ok in results)}/{len(results)} passed")
