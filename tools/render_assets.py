import asyncio
from playwright.async_api import async_playwright
from PIL import Image
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    async def shot(url,size,out,transparent=False):
      pg=await b.new_page(viewport={'width':size,'height':size})
      await pg.goto('file:///home/claude/shape-words/tools/'+url);await pg.wait_for_timeout(400)
      await pg.screenshot(path=out,omit_background=transparent,clip={'x':0,'y':0,'width':size,'height':size});await pg.close()
    await shot('icon.html',1024,'assets/icon-only.png')
    await shot('icon.html?mode=fg',1024,'assets/icon-foreground.png',True)
    await shot('icon.html?mode=bgonly',1024,'assets/icon-background.png')
    await shot('splash.html',2732,'assets/splash.png')
    await shot('splash.html?dark=1',2732,'assets/splash-dark.png')
    await b.close()
asyncio.run(main())
im=Image.open('assets/icon-only.png').convert('RGB');im.save('assets/icon-only.png')   # App Store icons may not have transparency
for f in ['splash.png','splash-dark.png','icon-background.png']:Image.open('assets/'+f).convert('RGB').save('assets/'+f)
print('ok')
