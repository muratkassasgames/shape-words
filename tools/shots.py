import asyncio,sys,os,mimetypes,json
sys.path.insert(0,'/home/claude/wh')
from playwright.async_api import async_playwright
from solver import find_path,board,trace
WWW='/home/claude/shape-words/www'
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=3)
    async def handle(route):
      u=route.request.url
      if u.startswith('http://app.test/blank'):await route.fulfill(body='<!doctype html><title>x</title>',content_type='text/html');return
      if u.startswith('http://app.test/'):
        f=os.path.join(WWW,u[len('http://app.test/'):].split('?')[0] or 'index.html')
        await route.fulfill(path=f,content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
      else:await route.abort()
    await ctx.route('**/*',handle)
    pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://app.test/index.html')
    words_all=await pg.evaluate("Object.keys(JSON.parse(document.getElementById('wh-audio').textContent))")
    async def setup(level,lang,learned=None,stars=None):
      st={'cur':level,'max':max(level,30),'stars':stars or {},'learned':learned or {},'clue':'en','voice':0,'lang':lang,'ts':1,'zoomTip':1}
      await pg.goto('http://app.test/blank.html')
      await pg.evaluate("s=>{localStorage.clear();localStorage.setItem('word-hunt-v2',JSON.stringify(s))}",st)
      await pg.goto('http://app.test/index.html');await pg.wait_for_timeout(500)
    async def clean():
      await pg.evaluate("document.querySelector('#toast').hidden=true");await pg.wait_for_timeout(250)
    async def play(k,bent_first=False,min_bent=0):
      n,g=await board(pg);cands=[]
      for w in words_all:
        path=find_path(g,n,w)
        if path:
          straight=len({(path[q][0]-path[q-1][0],path[q][1]-path[q-1][1]) for q in range(1,len(path))})==1
          cands.append((0 if (bent_first and not straight) else 1,-len(w),w,path))
      cands.sort();done=0;last=None
      for _,_,w,path in cands:
        if done>=k:break
        before=await pg.locator('.chip.done').count()
        await trace(pg,n,path);await pg.wait_for_timeout(120)
        if await pg.locator('.chip.done').count()>before:done+=1;last=w
      return last
    # 1 cover
    await setup(7,'en',{'LION':1,'APPLE':1,'WHALE':1,'MOON':1,'RAIN':1,'ROSE':1,'CAKE':1,'DOOR':1,'OAK':1,'PIANO':1,'GOLF':1,'MAP':1},{'1':3,'2':3,'3':3,'4':2,'5':3,'6':2})
    await pg.wait_for_timeout(900);await pg.screenshot(path='store/raw/1_cover.png')
    # 2 gameplay, Spanish
    await setup(3,'es');await pg.click('#continueBtn');await pg.wait_for_timeout(300)
    await play(3);await clean();await pg.screenshot(path='store/raw/2_learn.png')
    # 3 corner words
    await setup(110,'en');await pg.click('#continueBtn');await pg.wait_for_timeout(300)
    await play(5,bent_first=True);await clean();await pg.screenshot(path='store/raw/3_corners.png')
    # 4 big board, Turkish
    await setup(300,'tr');await pg.click('#continueBtn');await pg.wait_for_timeout(300)
    await play(4,bent_first=True);await clean();await pg.screenshot(path='store/raw/4_hard.png')
    # 5 win screen, German
    await setup(8,'de');await pg.click('#continueBtn');await pg.wait_for_timeout(300)
    await play(40);await pg.wait_for_timeout(2200);await pg.evaluate("document.querySelectorAll('#fx').forEach(c=>c.style.display='none')")
    await pg.screenshot(path='store/raw/5_win.png')
    # 6 word book, Chinese
    learned={w:1 for w in words_all[:40]}
    await setup(20,'zh',learned);await pg.click('#continueBtn');await pg.wait_for_timeout(300)
    await pg.click('#menuBtn');await pg.wait_for_timeout(200);await pg.click('#bookBtn');await pg.wait_for_timeout(300)
    await pg.screenshot(path='store/raw/6_book.png')
    print('errs',errs);await b.close()
asyncio.run(main())
