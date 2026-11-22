"""Builds www/ (the app's web content) from the published game page."""
import re, shutil, os, glob
SRC='/home/claude/word-hunt.html'; OUT='/home/claude/shape-words/www'
h=open(SRC).read()
def rep(a,b,cnt=1):
    global h
    assert h.count(a)==cnt,(h.count(a),a[:80]); h=h.replace(a,b)
# ---- fonts: bundle locally (latin + latin-ext, the weights the game uses) ----
css=[]
for fam,wts in [('fredoka',[500,600,700]),('nunito',[600,700,800])]:
    for w in wts:
        src=open(f'node_modules/@fontsource/{fam}/{w}.css').read()
        for block in re.findall(r'/\*[^*]*\*/\s*@font-face\s*\{[^}]*\}',src):
            sub=re.search(r'/\* [a-z]+-([a-z-]+)-\d+-normal \*/',block).group(1)
            if sub not in('latin','latin-ext'):continue
            for f in re.findall(r'url\(\./files/([^)]+\.woff2)\)',block):
                shutil.copy(f'node_modules/@fontsource/{fam}/files/{f}',f'{OUT}/fonts/{f}')
            block=re.sub(r'url\(\./files/([^)]+\.woff2)\) format\(\'woff2\'\),\s*url\(\./files/[^)]+\.woff\) format\(\'woff\'\)',r"url(fonts/\1) format('woff2')",block)
            block=block.replace("font-family: 'Fredoka'","font-family: 'Fredoka'").replace("font-display: swap","font-display: block")
            css.append(block)
open(f'{OUT}/fonts.css','w').write('\n'.join(css))
rep('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@600;700;800&display=swap">','<link rel="stylesheet" href="fonts.css">')
# ---- name ----
rep('<title>Word Hunt</title>','<title>Shape Words</title>')
rep('<meta name="claude:viewport-fit-sides" content="cover">\n','')
rep('<div class="en" id="learnEn">Word Hunt</div>','<div class="en" id="learnEn">Shape Words</div>')
rep('<h2>Word Hunt</h2>','<h2>Shape Words</h2>')
rep('aria-label="Word Hunt"','aria-label="Shape Words"',2)
rep('<div class="row"><span class="t" style="--i:0">W</span><span class="t" style="--i:1">O</span><span class="t" style="--i:2">R</span><span class="t" style="--i:3">D</span></div>\n      <div class="row hunt"><span class="t" style="--i:4">H</span><span class="t" style="--i:5">U</span><span class="t" style="--i:6">N</span><span class="t" style="--i:7">T</span></div>',
    '<div class="row"><span class="t" style="--i:0">S</span><span class="t" style="--i:1">H</span><span class="t" style="--i:2">A</span><span class="t" style="--i:3">P</span><span class="t" style="--i:4">E</span></div>\n      <div class="row hunt"><span class="t" style="--i:5">W</span><span class="t" style="--i:6">O</span><span class="t" style="--i:7">R</span><span class="t" style="--i:8">D</span><span class="t" style="--i:9">S</span></div>')
rep('.logo .t{width:clamp(46px,14vw,64px);','.logo .t{width:clamp(40px,12.4vw,60px);')
rep("font-size:clamp(28px,9vw,40px)","font-size:clamp(24px,8vw,38px)")
# ---- device storage: progress also kept in the app's native storage (Capacitor Preferences) ----
rep("""    if(!window.claude||!window.claude.use)return;
    const [db,user]=await Promise.all([window.claude.use('db'),window.claude.use('user')]);
    if(!db||!user)return;
    const id=await user.id();if(!id)return;
    const ref=db.doc('data/users/'+id+'/progress');""","""    const Pref=window.Capacitor&&window.Capacitor.Plugins&&window.Capacitor.Plugins.Preferences;
    if(!Pref)return;
    const ref={get:async()=>{const r=await Pref.get({key:'progress'});return{exists:!!(r&&r.value),data:()=>({json:r&&r.value})};},
               set:async(d)=>Pref.set({key:'progress',value:d.json})};""")
# ---- full document ----
reset='<style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000;-webkit-text-size-adjust:100%;overscroll-behavior:none}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style>'
doc='<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover"><meta name="format-detection" content="telephone=no">'+reset+'</head><body>\n'+h+'\n</body></html>'
open(f'{OUT}/index.html','w').write(doc)
print('www/index.html',round(len(doc)/1e6,2),'MB; fonts',len(os.listdir(OUT+'/fonts')))
