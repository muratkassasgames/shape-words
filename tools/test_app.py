import asyncio,sys,os,mimetypes
sys.path.insert(0,'/home/claude/wh')
from playwright.async_api import async_playwright
from solver import find_path,board,trace
WWW='/home/claude/shape-words/www'
MOCK="""
window.__pref=JSON.parse(localStorage.getItem('__pref')||'{}');window.__writes=0;
window.Capacitor={Plugins:{Preferences:{get:async({key})=>({value:window.__pref[key]??null}),
  set:async({key,value})=>{window.__pref[key]=value;window.__writes++;localStorage.setItem('__pref',JSON.stringify(window.__pref));}}}};
"""
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)
    await ctx.add_init_script(MOCK)
    ext=[]
    async def handle(route):
      u=route.request.url
      if u.startswith('http://app.test/'):
        f=os.path.join(WWW,u[len('http://app.test/'):].split('?')[0] or 'index.html')
        await route.fulfill(path=f,content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
      else:ext.append(u);await route.abort()
    await ctx.route('**/*',handle)
    pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://app.test/index.html');await pg.wait_for_timeout(900)
    await pg.screenshot(path='tools/app_cover.png')
    print('fonts loaded',await pg.evaluate("document.fonts.check('700 20px Fredoka') && document.fonts.check('800 14px Nunito')"))
    await pg.click('#startBtn');await pg.wait_for_timeout(300)
    n,g=await board(pg)
    words=await pg.evaluate("[...document.querySelectorAll('.chip .en')].map(c=>c.textContent)")
    for w in words[:3]:
      path=find_path(g,n,w);await trace(pg,n,path);await pg.wait_for_timeout(120)
    await pg.wait_for_timeout(1600)
    print('found',await pg.locator('.chip.done').count(),'pref writes',await pg.evaluate('window.__writes'))
    await pg.evaluate("localStorage.removeItem('word-hunt-v2')")
    await pg.goto('http://app.test/index.html');await pg.wait_for_timeout(900)
    print('after wiping web storage, cover says:',await pg.locator('#continueSub').text_content())
    print('external requests',ext,'errs',errs)
    await b.close()
asyncio.run(main())
