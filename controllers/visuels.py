# -*- coding: utf-8 -*-
# essayez quelque chose comme
def index():
    from base64 import b64encode
    import os
    #depid = request.args(0)
    deputes = list(mdb.deputes.find({'$and':[{'groupe_abrev':'REM'},{'stats.positions.exprimes':{'$lt':20}}]}))
    import random
    depute = deputes[random.randint(0,len(deputes))]
    
    path = os.path.join(request.folder, 'static/images/deputes/%s.jpg' % depute['depute_id'])
    photo = b64encode(open(path).read())
    s = depute['depute_nom'].split(' ')
    prenom = s[1]
    nom = ' '.join(s[2:])
    return dict(message="hello from visuels.py",id=depute['depute_shortid'],photo=photo,nom=nom,prenom=prenom,pct="%.2f %%" % depute['stats']['positions']['exprimes'])

def download():
    from base64 import b64encode
    import os
    depid = request.args(0)
    depute = mdb.deputes.find_one({'depute_shortid':depid})
    if not depute:
        depute = mdb.deputes.find_one({'depute_shortid':'jeanlucmelenchon'})

    path = os.path.join(request.folder, 'static/images/deputes/%s.jpg' % depute['depute_id'])
    photo = b64encode(open(path).read())
    s = depute['depute_nom'].split(' ')
    prenom = s[1]
    nom = ' '.join(s[2:])
    pct="%.2f %%" % depute['stats']['positions']['exprimes']
    inputsvg = str(svgvisuel('test',photo=photo,prenom=prenom,nom=nom,pct=pct))
    #result = cairosvg.svg2png(inputsvg,write_to=os.path.join(request.folder,'static/test.png'))
    from cStringIO import StringIO
    response.headers['ContentType'] ="application/octet-stream";
    response.headers['Content-Disposition']="attachment; filename="+depute['depute_shortid']+".svg"
    return response.stream(StringIO(inputsvg),chunk_size=4096)
