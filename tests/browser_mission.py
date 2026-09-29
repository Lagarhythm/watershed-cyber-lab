"""Optional live browser test for the guided mission. Start `python launch.py --port 8898`, then run this script.
Requires playwright and its Chromium installation (development only). Screenshots go to SHOTS (default /tmp/mission).
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
SHOTS=Path(os.environ.get('SHOTS','/tmp/mission')); SHOTS.mkdir(parents=True,exist_ok=True)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors,external=[],[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('dialog',lambda d:d.accept())
    def route(r):
        if r.request.url.startswith(('http://127.0.0.1:8898/','data:','blob:')): r.continue_()
        else: external.append(r.request.url); r.abort()
    page.route('**/*',route)
    page.goto('http://127.0.0.1:8898',wait_until='domcontentloaded')
    btn=lambda name: page.get_by_role('button',name=name,exact=True)
    def shot(n):
        page.wait_for_timeout(700)  # let reveal animations settle
        page.screenshot(path=str(SHOTS/f'{n}.png'),full_page=True)
    def finish_without_scrolling(action):
        """Run the action that completes a task and assert the page did not move."""
        before=page.evaluate('window.scrollY')
        action()
        page.locator('#gm-learned').wait_for()
        page.wait_for_timeout(400)
        assert page.evaluate('window.scrollY')==before, 'page scrolled after a task completed'
    def check_and_next(answer_text):
        page.locator('#gm-learned .gm-options button',has_text=answer_text).click()
        try: page.locator('.gm-options button.right').wait_for(timeout=5000)
        except Exception: page.screenshot(path=str(SHOTS/'FAIL.png'),full_page=True); raise
        page.locator('#gm-learned [data-action=next]').click()
        page.wait_for_timeout(300)

    btn('Start the mission →').wait_for(timeout=60000); shot('0-briefing')
    btn('Start the mission →').click()
    # 1 Observe
    btn('▶ Show network traffic').click()
    for h in ['portal-01','research-08','archive-01']:
        page.locator(f'[data-host={h}]').click(); page.locator('[data-label=normal]').click(); page.wait_for_timeout(150)
    page.locator('[data-host=research-07]').click(); page.get_by_text('First seen today at 09:14').wait_for()
    page.locator('[data-label=normal]').click(); page.locator('.gm-feedback.try').wait_for(); shot('1-observe-inspector')
    finish_without_scrolling(lambda: page.locator('[data-label=suspicious]').click()); shot('1-observe')
    check_and_next('It goes to a known website')
    # 2 Verify
    btn('Compute today’s fingerprints').click(); page.locator('.gm-fprow').first.wait_for()
    for f,v in [('research_notes.txt','match'),('collector_config.txt','changed'),('readme.txt','match')]:
        page.locator(f'[data-file="{f}"][data-verdict={v}]').click(); page.wait_for_timeout(150)
    page.locator('#gm-hash').fill('research sample'); page.wait_for_timeout(500); shot('2-integrity-changed')
    finish_without_scrolling(lambda: page.locator('#gm-hash').fill('Research sample'))
    check_and_next('The file was changed since the trusted list was made.')
    # 3 Decode
    page.locator('[data-open="readme.txt"]').click(); page.locator('.gm-feedback.try').wait_for()
    page.locator('[data-open="collector_config.txt"]').click()
    page.locator('[data-format=encrypted]').click(); page.locator('.gm-feedback.try').wait_for()
    page.locator('[data-format=base64]').click(); page.locator('.gm-json').wait_for()
    page.locator('[data-clue=host]').click(); page.wait_for_timeout(150); shot('3-decode-clues')
    page.locator('[data-clue=username]').click(); page.wait_for_timeout(150)
    finish_without_scrolling(lambda: page.locator('[data-clue=process]').click())
    check_and_next('No. Base64 is encoding')
    # 4 Connect
    page.locator('#gm-f-host').select_option('research-07'); page.get_by_text('Showing 24 of 54 records').wait_for()
    page.locator('#gm-f-proc').select_option('sync_agent'); page.get_by_text('Showing 8 of 54 records').wait_for(); shot('4-correlate-filtered')
    finish_without_scrolling(lambda: page.locator('[data-dest="203.0.113.77"]').click())
    check_and_next('Two independent sources agreeing')
    # 5 Contain
    page.locator('[data-host=portal-01]').click(); page.locator('[data-host=research-07]').click(); page.wait_for_timeout(200)
    btn('Test the connection').click(); page.locator('.gm-test.bad').wait_for(); shot('5-contain-overisolated')
    page.locator('[data-host=portal-01]').click(); page.wait_for_timeout(200)
    finish_without_scrolling(lambda: btn('Test the connection').click()); shot('5-contain')
    check_and_next('No. Isolation cuts its network connection')
    # 6 Repair (free typing)
    page.locator('#gm-user').fill('riley'); btn('Log in').click(); page.get_by_text('1 account matched',exact=True).wait_for()
    page.locator('#gm-user').fill("riley' OR '1'='1"); page.get_by_text('Red = your typing is now part of the command.').wait_for()
    btn('Log in').click(); page.get_by_text('3 accounts matched',exact=True).wait_for(); shot('6-repair-injection')
    page.locator('[data-mode=bound]').click(); page.wait_for_timeout(200)
    page.locator('#gm-user').fill("riley' OR '1'='1"); btn('Log in').click(); page.get_by_text('0 accounts matched',exact=True).wait_for()
    page.locator('#gm-user').fill("o'neil"); btn('Log in').click(); page.get_by_text('1 account matched',exact=True).wait_for(); shot('6-repair-fixed')
    finish_without_scrolling(lambda: btn('Apply the fix to the portal').click())
    check_and_next('It sends the input separately')
    # 7 Recover
    btn('Reconnect Research 07').click(); page.locator('.gm-feedback.try').wait_for()
    page.locator('[data-kill=browser]').click(); page.locator('.gm-feedback.try').wait_for()
    page.locator('[data-kill=sync_agent]').click(); page.wait_for_timeout(200)
    page.locator('[data-config=delete]').click(); page.locator('.gm-feedback.try').wait_for()
    page.locator('[data-config=restore]').click(); page.wait_for_timeout(200)
    btn('Reconnect Research 07').click(); page.wait_for_timeout(200)
    finish_without_scrolling(lambda: btn('Run final traffic check').click()); shot('7-recover')
    page.locator('#gm-learned [data-answer="1"]').click()
    btn('See your mission report →').click()
    page.get_by_text('Mission report').wait_for(); shot('8-debrief')
    assert page.locator('.gm-recap article').count()==7
    assert page.locator('.gm-log').count()==7

    page.set_viewport_size({'width':390,'height':844}); page.emulate_media(reduced_motion='reduce')
    shot('9-mobile-debrief')
    assert page.locator('.gm-shell').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1')
    page.locator('footer [data-action=reset]').click()
    btn('Start the mission →').wait_for(); btn('Start the mission →').click(); btn('▶ Show network traffic').click()
    page.locator('[data-host=research-07]').click(); page.wait_for_timeout(300)
    shot('9-mobile-observe')
    assert page.locator('.gm-shell').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1')
    assert not external,external
    assert not errors,errors
    print('Guided mission PASS: all 7 multi-part steps, wrong turns, no scroll on task completion, debrief, mobile, restart. Screenshots in',SHOTS)
    browser.close()
