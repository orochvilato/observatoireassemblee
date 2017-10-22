# -*- coding: utf-8 -*-
# essayez quelque chose comme
from base64 import b64encode
import requests
import os
def getvisuel(name,deputeid,**args):
    depute = mdb.deputes.find_one({'depute_shortid':deputeid})
    
    groupe = depute['groupe_abrev']
    if groupe == 'NI':
        groupe = depute['depute_election']['nuance']
    path = os.path.join(request.folder, 'static/images/deputes/%s.jpg' % depute['depute_id'])
    content = open(path).read()
    #content =requests.get('http://www2.assemblee-nationale.fr/static/tribun/15/photos/'+depute['depute_uid'][2:]+'.jpg').content
    photo = b64encode(content)
    s = depute['depute_nom'].split(' ')
    prenom = s[1]
    nom = ' '.join(s[2:])
    id = depute['depute_shortid']
    pct = ("%.2f%%" % depute['stats']['positions']['exprimes']).replace('.',',')
    import datetime
    import re
    symbol = XML(response.render('svg/symbols/vote.svg', color='#82cde2',tx=354,ty=150,scale=0.4))
    svg = svgvisuel(name,symbol=symbol,photo=photo,prenom=prenom,nom=nom,pct=pct,groupe=groupe,depart=int(depute['depute_departement_id']),date=datetime.datetime.now().strftime('%d/%m/%Y'))
    data = str(svg)
    w,h = re.search(r'viewBox="0 0 ([0-9\.]+) ([0-9\.]+)"',data).groups()
    w = float(w)
    h = float(h)
    coef = float(h/w)
    return dict(data=svg,coef=coef)

def index():
    from base64 import b64encode
    import requests
    import os
    depute = request.args(0)
    tweet = (request.args(1)=='tweet')
    hasard = False
    if not depute:
        hasard = True
        deputes = list(mdb.deputes.find({'$and':[{'depute_actif':True},{'stats.positions.exprimes':{'$lt':20}}]}))
        import random
        depute = deputes[random.randint(0,len(deputes)-1)]['depute_shortid']
    return dict(tweet=tweet,visuel=getvisuel('test2',depute),id=depute,hasard=hasard)


def getimage(deputeid,w,h):
    
    from selenium import webdriver
    
    driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true']) # or add to your PATH
    driver.set_window_size(w,h)# optional
    driver.get(URL('index',args=[deputeid,'tweet'],scheme=True, host=True))
    data = driver.get_screenshot_as_png()
    return data

def tweeter():
    from TwitterAPI import TwitterAPI
    api = TwitterAPI('Ym8iy6cdZcr00D3cQ4I3nH6M5', 'OOMiTg1ezrX6aY8w5N6UMKMZe9BgmJLT6udnjfTEZ6NBOvlblm','3434108799-IzoPtfb1jPnMkStVZyDaDJ2Fa8iiBijfJMnNF99', 'MiMOaX9D8CYH7nIWPbJjlYgGHSUGTmKpwVH9FdV0GC6Rj')
    id = request.args(0)
    w = request.args(1)
    h = request.args(2)
    
    data = getimage(id,w,h)
    r = api.request('statuses/update_with_media', {'status':'post'}, {'media': data})
    if r.status_code == 200:
        picurl = r.json()['extended_entities']['media'][0]['display_url']
        import urllib
        params = urllib.urlencode({'text':'---Votre message---   '+picurl})
        redirect('https://twitter.com/intent/tweet?'+params)
   
    #r = api.request('statuses/update_with_media', {'status':message},{'media[]':data})
    #redirect('https://twitter.com/orochvilato?lang=fr')
    return BEAUTIFY(r.json())
    


def download():
    from base64 import b64encode
    import os
    depid = request.args(0)
    width = request.args(1)
    height = request.args(2)
    if width:
        data = getimage(depid,int(width),int(height))
        compl = "%sx%s" % (width,height)
        ext = 'png'
    else:
        visuel = getvisuel('test2',depid)
        data = str(visuel['data'])
        compl = ""
        ext = "svg"
        
    from cStringIO import StringIO
    response.headers['ContentType'] ="application/octet-stream";
    response.headers['Content-Disposition']="attachment; filename="+depid+compl+"."+ext

    return response.stream(StringIO(data),chunk_size=4096)
