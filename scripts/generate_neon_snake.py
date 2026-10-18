#!/usr/bin/env python3
"""Generate a glowing animated contribution snake GIF from GitHub GraphQL data."""
import json, os, urllib.request
from pathlib import Path
from datetime import date
from PIL import Image, ImageDraw, ImageFilter

USER = os.getenv('GITHUB_USERNAME', 'raghav4444')
TOKEN = os.getenv('GITHUB_TOKEN', '')
OUT = Path('dist'); OUT.mkdir(exist_ok=True)
COLS, ROWS, CELL, GAP, PAD, HEADER = 53, 7, 12, 4, 22, 42
W = PAD*2 + COLS*(CELL+GAP)-GAP
H = HEADER + PAD*2 + ROWS*(CELL+GAP)-GAP
BG=(2,8,5); NEON=(57,255,20); CORE=(220,255,200)
LEVELS=[(7,20,12),(11,43,18),(15,101,31),(25,183,53),(57,255,20)]
FRAMES=112; SNAKE_LEN=9

def contributions():
    if not TOKEN: raise RuntimeError('GITHUB_TOKEN is required.')
    q='''query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{weeks{contributionDays{contributionCount date}}}}}}'''
    body=json.dumps({'query':q,'variables':{'login':USER}}).encode()
    req=urllib.request.Request('https://api.github.com/graphql',data=body,headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'application/json','User-Agent':'neon-predator-snake'})
    with urllib.request.urlopen(req,timeout=30) as r: data=json.loads(r.read())
    if data.get('errors') or not data.get('data',{}).get('user'): raise RuntimeError(str(data.get('errors','GitHub user not found')))
    weeks=data['data']['user']['contributionsCollection']['contributionCalendar']['weeks'][-COLS:]
    grid=[[0]*ROWS for _ in range(COLS)]
    for x,week in enumerate(weeks):
        for day in week['contributionDays']:
            dt=date.fromisoformat(day['date']); y=(dt.weekday()+1)%7
            grid[x][y]=int(day['contributionCount'])
    maximum=max((n for col in grid for n in col),default=1) or 1
    return [[0 if n==0 else min(4,1+int(n/maximum*3.99)) for n in col] for col in grid]

def route():
    return [(x,y) for y in range(ROWS) for x in (range(COLS) if y%2==0 else range(COLS-1,-1,-1))]

def xy(x,y): return PAD+x*(CELL+GAP), HEADER+PAD+y*(CELL+GAP)

def render(grid, points, frame):
    im=Image.new('RGBA',(W,H),BG+(255,)); d=ImageDraw.Draw(im)
    d.text((PAD,13),'CONTRIBUTION MATRIX',fill=(117,170,128)); d.text((W-PAD-96,13),'NEON / LIVE',fill=NEON)
    d.rounded_rectangle((5,5,W-6,H-6),radius=12,outline=(13,42,22),width=1)
    for x in range(COLS):
        for y in range(ROWS):
            px,py=xy(x,y); c=LEVELS[grid[x][y]] if grid[x][y] else (7,20,12)
            d.rounded_rectangle((px,py,px+CELL,py+CELL),radius=3,fill=c+(255,))
    head=(frame*3)%len(points)
    glow=Image.new('RGBA',im.size,(0,0,0,0)); gd=ImageDraw.Draw(glow)
    for tail in range(SNAKE_LEN,0,-1):
        x,y=points[(head-tail)%len(points)]; px,py=xy(x,y)
        a=int(190*(1-tail/(SNAKE_LEN+1))**1.25)
        gd.rounded_rectangle((px-3,py-3,px+CELL+3,py+CELL+3),radius=6,fill=NEON+(a,))
    im=Image.alpha_composite(im,glow.filter(ImageFilter.GaussianBlur(7))); d=ImageDraw.Draw(im)
    for tail in range(SNAKE_LEN,0,-1):
        x,y=points[(head-tail)%len(points)]; px,py=xy(x,y); a=max(70,255-tail*20)
        d.rounded_rectangle((px+2,py+2,px+CELL-2,py+CELL-2),radius=3,fill=(24,200,24,a))
    x,y=points[head]; px,py=xy(x,y)
    hg=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(hg).ellipse((px-8,py-8,px+CELL+8,py+CELL+8),fill=NEON+(240,))
    im=Image.alpha_composite(im,hg.filter(ImageFilter.GaussianBlur(8))); d=ImageDraw.Draw(im)
    d.rounded_rectangle((px+1,py+1,px+CELL-1,py+CELL-1),radius=4,fill=CORE+(255,),outline=NEON+(255,),width=2)
    for k in range(3):
        if (frame+k*9)%7<2:
            sx=px+CELL//2+((frame*(k+2)+k*11)%17)-8; sy=py+CELL//2+((frame*(k+3)+k*7)%17)-8
            d.ellipse((sx,sy,sx+2,sy+2),fill=CORE+(255,))
    return im.convert('P',palette=Image.Palette.ADAPTIVE,colors=256)

def main():
    grid=contributions(); points=route(); frames=[render(grid,points,i) for i in range(FRAMES)]
    frames[0].save(OUT/'neon-snake.gif',save_all=True,append_images=frames[1:],duration=55,loop=0,optimize=True,disposal=2)
    # Scalable static grid preview; GIF is the reliable animated README asset.
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" rx="12" fill="#020805"/>','<defs><filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>']
    parts += [f'<text x="{PAD}" y="26" fill="#75aa80" font-family="monospace" font-size="12">CONTRIBUTION MATRIX</text>']
    for x in range(COLS):
        for y in range(ROWS):
            px,py=xy(x,y); c=LEVELS[grid[x][y]] if grid[x][y] else (7,20,12); color='#%02x%02x%02x'%c
            parts.append(f'<rect x="{px}" y="{py}" width="{CELL}" height="{CELL}" rx="3" fill="{color}"/>')
    parts.append('</svg>'); (OUT/'neon-snake.svg').write_text('\n'.join(parts))
    print('Generated dist/neon-snake.gif and dist/neon-snake.svg')
if __name__=='__main__': main()
