"""Optional live browser test. Start `python launch.py --port 8898`, then run this script.
Requires playwright and its Chromium installation (development only).
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
PREVIEWS=Path(__file__).resolve().parents[1]/'docs'/'previews'

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1512,'height':1300})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    external=[]
    def route(request):
        if request.request.url.startswith(('http://127.0.0.1:8898/', 'data:', 'blob:')): request.continue_()
        else: external.append(request.request.url);request.abort()
    page.route('**/*',route)
    page.goto('http://127.0.0.1:8898',wait_until='domcontentloaded')
    page.get_by_role('button',name='Start simulation',exact=True).wait_for(timeout=60000)
    page.screenshot(path='/tmp/watershed-operations.png',full_page=True)
    print('Initial interface rendered; JS errors:',errors)
    page.get_by_role('button',name='Start simulation',exact=True).click()
    page.locator('#ws-speed').select_option('4')
    page.wait_for_function("document.querySelector('#ws-beacons').textContent.includes('1 ')",timeout=10000)
    page.get_by_role('button',name='Pause',exact=True).click()
    page.locator('[data-tab=evidence]').click()
    page.get_by_role('button',name='Verify files',exact=True).click()
    page.get_by_text('Changed',exact=True).wait_for()
    page.locator('#ws-artifact').select_option('collector_config.txt')
    page.get_by_role('button',name='Decode selected file',exact=True).click()
    page.get_by_text('SYS-042',exact=True).first.wait_for()
    page.locator('#ws-c-host').select_option('research-07')
    page.locator('#ws-c-process').select_option('sync_agent')
    page.locator('#ws-c-destination').select_option('203.0.113.77')
    page.get_by_role('button',name='Check correlation',exact=True).click()
    page.get_by_text('CORRELATION VERIFIED',exact=True).wait_for()
    page.screenshot(path=str(PREVIEWS/'evidence.png'),full_page=True)
    page.locator('[data-tab=operations]').click()
    page.get_by_role('button',name='Isolate host',exact=True).click()
    page.wait_for_function("document.querySelector('#ws-availability').textContent==='75%'")
    page.locator('[data-tab=response]').click()
    page.get_by_role('button',name='Insert test payload',exact=True).click()
    page.get_by_role('button',name='Run lookup',exact=True).click()
    page.get_by_text('3 matching users',exact=True).wait_for()
    page.locator('input[value=bound]').check()
    page.get_by_role('button',name='Run lookup',exact=True).click()
    page.get_by_text('0 matching users',exact=True).wait_for()
    page.get_by_role('button',name='Apply portal repair',exact=True).click()
    page.get_by_role('button',name='Portal repaired ✓',exact=True).wait_for()
    page.locator('[data-tab=operations]').click()
    page.get_by_role('button',name='Remove simulated process',exact=True).click()
    page.get_by_role('button',name='Process removed ✓',exact=True).wait_for()
    page.get_by_role('button',name='Restore host',exact=True).click()
    page.wait_for_function("document.querySelector('#ws-availability').textContent==='100%'")
    page.locator('[data-tab=debrief]').click()
    page.get_by_role('button',name='Finish attempt & review',exact=True).click()
    page.get_by_text('FINAL OBJECTIVE SCORE',exact=True).wait_for()
    assert page.locator('.ws-score>strong').inner_text()=='100/100'
    page.screenshot(path=str(PREVIEWS/'debrief.png'),full_page=True)
    page.reload(wait_until='domcontentloaded')
    page.get_by_role('button',name='Resume saved attempt',exact=True).wait_for(timeout=60000)
    page.get_by_role('button',name='Resume saved attempt',exact=True).click()
    page.get_by_text('Attempt complete',exact=True).wait_for()
    page.locator('[data-tab=debrief]').click()
    assert page.locator('.ws-score>strong').inner_text()=='100/100'
    page.get_by_role('button',name='Start a new attempt',exact=True).click()
    page.get_by_role('button',name='Reset this attempt',exact=True).click()
    page.wait_for_function("document.querySelector('#ws-progress').textContent==='0/5'")
    page.locator('[data-tab=operations]').click()
    page.get_by_role('button',name='Start simulation',exact=True).click()
    page.locator('#ws-speed').select_option('4')
    page.wait_for_function("parseInt(document.querySelector('#ws-beacons').textContent)>=3")
    page.get_by_role('button',name='Pause',exact=True).click()
    page.screenshot(path=str(PREVIEWS/'operations.png'),full_page=True)
    with page.expect_download() as download:
        page.locator('[data-tab=debrief]').click()
        page.get_by_role('button',name='Download report',exact=True).click()
    assert download.value.suggested_filename=='watershed-incident-report.json'
    page.set_viewport_size({'width':390,'height':844})
    page.emulate_media(reduced_motion='reduce')
    page.locator('[data-tab=operations]').click()
    page.screenshot(path='/tmp/watershed-mobile.png',full_page=True)
    assert page.locator('.ws-shell').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1')
    assert page.locator('[data-host="research-08"]').get_attribute('aria-pressed')=='false'
    page.locator('[data-host="research-08"]').focus()
    page.keyboard.press('Enter')
    page.wait_for_function("document.querySelector('[data-host=\"research-08\"]').getAttribute('aria-pressed')==='true'")
    assert not external,external
    assert not errors,errors
    print('Full student path PASS: evidence, live tick, isolation, query experiments, patch, recovery, score 100.')
    browser.close()
