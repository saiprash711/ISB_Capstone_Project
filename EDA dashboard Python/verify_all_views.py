import sys
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.edge.options import Options
import time, json

opts = Options()
opts.add_argument('--headless')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=1920,1200')
driver = webdriver.Edge(options=opts)
driver.get('http://localhost:8501')
time.sleep(5)

# 1. Dark mode cockpit screenshot
driver.save_screenshot('verified_dark_cockpit.png')
print('Captured verified_dark_cockpit.png')

# 2. Inspect dark mode buttons
js_inspect_btns = """
let res = [];
document.querySelectorAll('[data-testid="stButtonGroup"] button').forEach(b => {
    let cs = window.getComputedStyle(b);
    let p = b.querySelector('p') || b;
    let pcs = window.getComputedStyle(p);
    res.push({
        text: b.innerText,
        checked: b.getAttribute('aria-checked'),
        btnBg: cs.backgroundColor,
        btnColor: cs.color,
        pColor: pcs.color
    });
});
return res;
"""
dark_btns = driver.execute_script(js_inspect_btns)
print('Dark Mode ButtonGroup buttons:')
for b in dark_btns[:4]:
    print(' ', b)

# 3. Switch to Light Mode
driver.execute_script("""
document.querySelectorAll('button').forEach(b => {
    if (b.innerText.includes('Light')) b.click();
});
""")
time.sleep(4)

# 4. Light mode cockpit screenshot
driver.save_screenshot('verified_light_cockpit.png')
print('Captured verified_light_cockpit.png')

light_btns = driver.execute_script(js_inspect_btns)
print('Light Mode ButtonGroup buttons:')
for b in light_btns[:4]:
    print(' ', b)

# 5. Check other pages in Light Mode
pages = [
    ("Forecasting", "AI Demand Forecasting", "verified_light_forecasting.png"),
    ("Radar", "Data Quality Radar", "verified_light_radar.png"),
    ("Cleaning", "Data Cleaning Studio", "verified_light_cleaning.png"),
    ("Statistical", "Statistical Deep-Dive", "verified_light_statistical.png"),
    ("Explorer", "Intelligence Explorer", "verified_light_explorer.png"),
    ("Reports", "C-Suite Reports", "verified_light_reports.png")
]

for shortname, label, fname in pages:
    driver.execute_script(f"""
    document.querySelectorAll('button').forEach(b => {{
        if (b.innerText.includes('{label}')) b.click();
    }});
    """)
    time.sleep(3)
    driver.save_screenshot(fname)
    print(f"Captured {fname}")

driver.quit()
print('All verifications completed successfully!')
