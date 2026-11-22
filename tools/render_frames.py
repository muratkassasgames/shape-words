import asyncio,urllib.parse
from playwright.async_api import async_playwright
from PIL import Image
S=[('1_cover.png','Learn English with word puzzles','7 languages · 500 levels · free','linear-gradient(160deg,#ff8db5,#d9467f)'),
   ('2_learn.png','Find the word, learn its meaning','Translation in your language','linear-gradient(160deg,#5cc6f2,#1f7fc9)'),
   ('3_corners.png','Words turn corners','L shapes, U shapes and squares','linear-gradient(160deg,#b98cff,#6d3fd6)'),
   ('2_learn.png','Hear native pronunciation','American English voice for 796 words','linear-gradient(160deg,#ffb84d,#e0762a)'),
   ('4_hard.png','500 levels that get harder','Bigger boards, more words, fake look-alikes','linear-gradient(160deg,#4cc98a,#1f7a52)'),
   ('6_book.png','Your own word book','Every word you find, ready to review','linear-gradient(160deg,#ffcf5c,#d9932a)')]
TARGETS=[('ios',1320,2868,860),('android',1080,1920,600)]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for name,W,H,sw in TARGETS:
      for k,(img,t,st,bg) in enumerate(S,1):
        pg=await b.new_page(viewport={'width':W,'height':H})
        url='file:///home/claude/shape-words/tools/frame.html?'+urllib.parse.urlencode({'w':W,'h':H,'sw':sw,'img':img,'t':t,'st':st,'bg':bg})
        await pg.goto(url);await pg.wait_for_timeout(500)
        out=f'store/{name}/{k}.png'
        import os;os.makedirs(f'store/{name}',exist_ok=True)
        await pg.screenshot(path=out);await pg.close()
        Image.open(out).convert('RGB').save(out)
    await b.close()
asyncio.run(main())
