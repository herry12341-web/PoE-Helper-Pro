"""Run with Vite serving: python tests/ui_smoke.py [base_url]. Requires Python playwright + Chromium."""
import json, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/acts_data.json').read_text())
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':400,'height':780})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script("if(!localStorage.getItem('poe_helper_config'))localStorage.setItem('poe_helper_config',JSON.stringify({activeGuideId:'poe1',last_act:0}));")
    page.goto(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:5173')
    for act in range(1,11):
        expect(page.locator('.campaign-heading')).to_contain_text(f'A{act} 地圖')
        zone=next(z for z in data['zones'] if z['act']==act and z['map_images'])
        page.get_by_label('選擇區域').select_option(zone['zone_id'])
        image=page.locator('.campaign-gallery img').first
        expect(image).to_be_visible();page.wait_for_function("document.querySelector('.campaign-gallery img')?.naturalWidth > 0")
        assert page.get_by_test_id('gem-purchases').count()==0
        if act==1:
            page.get_by_label('選擇區域').select_option('a1-coast')
            page.locator('.campaign-gallery button').first.hover();expect(page.locator('.campaign-hover')).to_be_visible()
            page.locator('.campaign-gallery button').nth(1).click();expect(page.get_by_role('dialog')).to_be_visible()
            expect(page.get_by_role('dialog')).to_contain_text('2/8')
            before=page.locator('.poe-viewer-stage img').get_attribute('style');page.get_by_role('dialog').dispatch_event('wheel',{'deltaY':-100});page.wait_for_function('(old) => document.querySelector(".poe-viewer-stage img").getAttribute("style") !== old',arg=before)
            page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0)
        if act==6:
            page.get_by_label('選擇區域').select_option('a6-lioneyes-watch');expect(page.get_by_test_id('gem-purchases')).to_be_visible()
            page.get_by_test_id('gem-purchases').get_by_role('checkbox').check()
            page.reload();page.get_by_label('選擇區域').select_option('a6-lioneyes-watch');expect(page.get_by_test_id('gem-purchases').get_by_role('checkbox')).to_be_checked()
        for width in (300,400,800):
            page.set_viewport_size({'width':width,'height':780})
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), f'overflow Act {act} width {width}'
        page.set_viewport_size({'width':400,'height':780})
        print(f'PASS Act {act}: maps, reminders, responsive widths',flush=True)
        if act<10:page.get_by_role('button',name='下一章',exact=True).click()
    assert not errors,errors
    browser.close()
print('PASS all browser checks')
