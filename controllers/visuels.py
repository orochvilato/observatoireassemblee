# -*- coding: utf-8 -*-
# essayez quelque chose comme
from base64 import b64encode
import requests
import json
import os
import re
import datetime
import xmltodict
CACHE_TIME = 0
nuances = dict([('DIV', 'Divers'), ('ECO', 'Ecologiste'), ('EXG', 'Extrème gauche'), ('FN', 'Front National'), ('DVD', 'Divers droite'), ('FI', 'La France insoumise'), ('LR', u'Les Républicains'), ('COM', u'Parti communiste fran\xc3\xa7ais'), ('REM', u'La République en marche'), ('SOC', 'Parti socialiste'), ('DLF', 'Debout la France'), ('DVG', 'Divers gauche'), ('EXD', 'Extrème droite'), ('REG', u'Régionalistes'), ('UDI', u'Union des Démocrates et Indépendants'), ('MDM', 'Modem'), ('RDG', 'Parti radical de gauche')])

filtres_data = {'groupe':[(g['groupe_abrev'],g['groupe_libelle']) for g in mdb.groupes.find({},{'groupe_libelle':1,'groupe_abrev':1})],
                'pct':{'0 à 10%':0,'10 à 20%':1,'20 à 30%':2,'30 à 40%':3,'40 à 50%':4,'50 à 60%':5,'60 à 70%':6,'70 à 80%':7,'80 à 90%':8,'90 à 100%':9},
                   'vote':{'pour':0,'contre':1,'abstention':2,'absent':3}}


domaines = {'discord':{'nom':'Discord',
                       'champs':{'site':'discord-insoumis.fr'},
                       'couleurs':{'c_fond':'#fafafa',
                            'c_bandeau1':'#c9462c',
                            'c_textebandeau1':'#ffffff',
                            'c_bandeau2':'#04b4c7',
                            'c_textebandeau2':'#ffffff',
                            'c_bandeau3':'#82cde2', #'#23B9D0',
                            'c_date':'#ffffff',
                            'c_site':'#ffffff'}},
              'observatoire':{'nom':'Observatoire',
                              'champs':{'site':'observatoire-democratie.fr'},
                              'couleurs':{'c_fond':'#fffcf0',
                                'c_bandeau3':'#82cde2',
                                'c_bandeau2':'#ff0052',
                                'c_bandeau1':'#213659',
                                'c_date':'#213659',
                                'c_site':'#213659',
                                'c_textebandeau1':'#ffffff',
                                'c_textebandeau2':'#ffffff',
                                }}
           }
stats = {'participation':('stats.positions.exprimes','pct'),
         'presencecom':('stats.commissions.present','pct'),
         'vote.isf':('depute_votes_cles.169','vote'),
         'vote.ordonnances':('depute_votes_cles.106','vote')}

prefiltres = { 
    'deputepart20':{'stats.positions.exprimes':{'$lt':20}},
    'deputepart20rem':{'$and':[{'groupe_abrev':'REM'},{'stats.positions.exprimes':{'$lt':20}}]},
    'deputepres20rem':{'$and':[{'groupe_abrev':'REM'},{'stats.commissions.present':{'$lt':20}}]},
    'voteisf':{'depute_votes_cles.169':{'$in':['pour','contre']}},
    'voteordonnances':{'depute_votes_cles.106':{'$in':['pour','contre']}},
    }

listes = {
            'statdepute': { 'collection':'deputes',
                            'cle':'depute_shortid',
                            'filtres':[('groupe','string')],
                            'champs':[('nom','depute_nomcomplet'),('groupe','groupe_libelle')]}
         }
donnees = {
            'depute':{  'groupe':'depute_groupe',
                        'nom':'depute_nom',
                        'prenom':'depute_prenom',
                        'photo':'depute_photo',
                        }
          }

visuels = [ dict(base="base1",path='observatoire.stats.participation',visuel='participation',nom='Participation aux scrutins publics',domaine='observatoire',donnees='depute',liste='statdepute',stat='participation',ratio=2,default=45),
            dict(base="base1",path='observatoire.stats.presencecomm',visuel='presencecomm',nom='Présence en commission',domaine='observatoire',donnees='depute',liste='statdepute',stat='presencecom',ratio=2,default=45),
            dict(base="base1",path='observatoire.votes.voteordonnances',visuel='voteordonnances',nom='Reforme du code du travail par ordonnances',domaine='observatoire',donnees='depute',liste='statdepute',stat='vote.ordonnances',svgdata='position',prefiltre='voteordonnances',ratio=2,default='contre'),
            dict(base="base1",path='observatoire.votes.voteisf',visuel='voteisf',nom="Suppression de lʹISF",domaine='observatoire',donnees='depute',liste='statdepute',stat='vote.isf',svgdata='position',prefiltre='voteisf',ratio=2,default='pour'),
            dict(base="base2",path='discord.presencecomrem',visuel='presencecomrem',nom='Présence en commission (REM) (<20%)',domaine='discord',donnees='depute',liste='statdepute',stat='presencecom',prefiltre='deputepres20rem',ratio=2,default=15),
            dict(base="base3",path='discord.presencecomrem2',visuel='presencecomrem2',nom='Présence en commission (REM) (<20%)',domaine='discord',donnees='depute',liste='statdepute',stat='presencecom',prefiltre='deputepres20rem',ratio=2,default=15),
            dict(base="base2",path='discord.participationrem',visuel='participationrem',nom='Participation aux scrutins publics (REM)   (<20%)',domaine='discord',donnees='depute',liste='statdepute',stat='participation',prefiltre="deputepart20rem",ratio=2,default=15),
           dict(base="base3",path='discord.participationrem2',visuel='participationrem2',nom='Participation aux scrutins publics (REM)   (<20%)',domaine='discord',donnees='depute',liste='statdepute',stat='participation',prefiltre="deputepart20rem",ratio=2,default=15),
            dict(base="base1",path='discord.participationcocotier',visuel='participationcocotier',nom='Participation aux scrutins publics (<20%)',domaine='discord',donnees='depute',liste='statdepute',stat='participation',prefiltre='deputepart20',ratio=2,default=12)
            ]
vlabels = {'discord':'Discord','observatoire':'Observatoire','votes':'Votes','stats':'Stats'}

def ajax_liste():
    try:
        page = int(request.args(0))
        visuel_idx = int(request.vars.get('visuel','0'))
        groupe = request.vars.get('groupe','')
    except:
        page = 0
        idx = 0
        
    
    nbitems = 20
    filtres_data = {'groupe':dict([ (g['groupe_libelle'],g['groupe_abrev']) for g in mdb.groupes.find({},{'groupe_libelle':1,'groupe_abrev':1})]),
                'pct':{'0 à 10%':0,'10 à 20%':1,'20 à 30%':2,'30 à 40%':3,'40 à 50%':4,'50 à 60%':5,'60 à 70%':6,'70 à 80%':7,'80 à 90%':8,'90 à 100%':9},
                   'vote':{'pour':0,'contre':1,'abstention':2,'absent':3}}

    visuel = visuels[visuel_idx]
    stat = stats[visuel['stat']]
    datasrc=listes[visuel['liste']]
    prefiltre = prefiltres.get(visuel.get('prefiltre',None),None)
    if datasrc['collection']=='deputes':
        filtre = {'$and':[{'depute_actif':True}]}
        if groupe:
            filtre['$and'].append({'groupe_abrev':groupe})
    if prefiltre:
        if '$and' in filtre.keys():
            filtre['$and'].append(prefiltre)
        else:
            filtre = prefiltre
    
    cle = listes[visuels[visuel_idx]['liste']]['cle']
    fields = dict((k,1) for k in dict(datasrc['champs']).values() + [stat[0],cle])
    data = list(mdb[datasrc['collection']].find(filtre,fields).sort(stat[0],-1).skip(page*nbitems).limit(nbitems))
    
        
    return dict(visuel_idx=visuel_idx, visuel=visuel, stat=stat,champs = dict(datasrc['champs']+[(visuel['stat'],stat[0])]),cle=cle,items=data,lastpage=(len(data)<nbitems))

def get_visudata(source,key,**args):
    if key=='depute_groupe':
        groupe_abrev = source['groupe_abrev']
        if groupe_abrev == 'NI':
            groupe_abrev = source['depute_election']['nuance']
            groupe_lib = nuances[groupe_abrev]
        else:
            groupe_lib = source['groupe_libelle'].split(':')[0].strip()
        depart = source['depute_departement_id'] if source['depute_departement_id'][0]!='0' else source['depute_departement_id'][1:]
        groupe = u"Député %s (%s) - %s" % (groupe_lib,groupe_abrev,depart)
        return groupe
    elif key=='depute_photo2':
        path = os.path.join(request.folder, 'static/images/deputes/%s.jpg' % source['depute_id'])
        content = open(path).read()
        #content =requests.get('http://www2.assemblee-nationale.fr/static/tribun/15/photos/'+depute['depute_uid'][2:]+'.jpg').content
        photo = b64encode(content)
        return photo
    elif key=='depute_nom':
        return source['depute_hatvp'][0]['nom']
    elif key=='depute_prenom':
        return source['depute_hatvp'][0]['prenom']
    elif "stats." in key:
        return int(round(getdot(source,key),0))
    else:
        return getdot(source,key)
    
def voirVisuel():
    try:
        idx = int(request.args(0))
        items = request.args[1:]
    except:
        idx = 0
        items = ['modele']
    return dict(idx=idx,items=items)


def getVisuel():
    try:
        idx = int(request.args(0))
        visuel = visuels[idx]
        key = request.args(1) or 'modele'
        format = request.extension
        baseonly = request.vars.get('baseonly',False)
        liste = listes[visuel['liste']]
        ext = {'stat':visuel['default']}
        if key!='modele':
            data = mdb[liste['collection']].find_one({liste['cle']:key})
            if data:
                ext = dict((k,get_visudata(data,v)) for k,v in donnees[visuel['donnees']].iteritems())
                if baseonly:
                    ext['baseonly'] = True
                ext['stat']=get_visudata(data,stats[visuel['stat']][0])

        download = request.vars.get('download',False)
        w = request.vars.get('w',None)
        h = request.vars.get('h',None)

    #else:   
    except:
        idx = 0
        visuel = visuels[0]
        format = 'svg'
        idx = 0
        w = 1024
        h = 512
        key = 'modele'
    
    
    def getdata():
        if format=='png':
            w = request.vars.get('w',None)
            h = request.vars.get('h',None)

            from selenium import webdriver
            driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
            if not w:
                if not h:
                    h = 512
                w=h*visuel['ratio']
            else:
                h=w/visuel['ratio']
            

            driver.set_window_size(w,h)# optional
            driver.get(URL('getVisuel.svg',args=[idx,key],scheme=True, host=True))
            data = driver.get_screenshot_as_png()
        else:
            from cStringIO import StringIO
            data=get_visuel_final(visuels[idx],**ext)
        return data
    
    
    if download:
        response.headers['Content-Disposition']="attachment; filename=%s-%s-%s-%s.%s" % (visuel['domaine'],visuel['donnees'],visuel['visuel'],key,format)
    if format=='png':
        response.headers['Content-Type'] ="image/png"
    elif format=='svg':
        response.headers['Content-Type'] ="image/svg+xml"
    
    response.headers['Accept-Ranges'] = "bytes"
    #response.headers['Cache-Control']=''
    #response.headers['Expires']=''
    
    data = cache.ram(request.env.path_info,lambda:getdata(),time_expire=CACHE_TIME)
    response.headers['Content-Length'] = len(data)
    return data
    
    #response.headers['Content-Disposition']="attachment; filename="+depid+compl+"."+ext


def subsvg(content_path):
    content_svg = xmltodict.parse(open(content_path).read())
    from string import Template
    g = content_svg['svg']['g']
    return xmltodict.unparse({'g':g},full_document=False)
    
def get_visuel_final(visuel,baseonly=False,**_elts):
    base = visuel['base']
    domaine = visuel['domaine']
    visuelname = visuel['visuel']
    
    if 'svgdata' in visuel.keys() and 'stat' in _elts.keys():
        svgdata_path = os.path.join(request.folder, 'views', 'visuels','svgdata',visuel['svgdata'],domaine,'%s.svg' % _elts['stat'])
        svgdata = subsvg(svgdata_path)
    else:
        svgdata = ""
    content_path = os.path.join(request.folder, 'views', 'visuels','contenus',base,domaine,'%s.svg' % visuelname)
    content_svg = subsvg(content_path)
    from string import Template
    contenu = XML(Template(content_svg).substitute(**_elts)+svgdata)
    couleurs = domaines[domaine]['couleurs']
    
    elts ={'nom':'DUPONT',
           'prenom':'Jean-Claude',
            'groupe':'Député Les doux réveurs (42)',
            'photo':"""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
"""}
    elts.update(_elts)    
    data = domaines[domaine]['champs']
    data.update(couleurs)
    data.update(elts)
    data['date'] = 'Généré le %s' % datetime.datetime.now().strftime('%d/%m/%Y')
    data['contenu'] = contenu if not baseonly else ""
    return get_visuel('bases/%s' % base,**data)

def generer():
    visuels_tree = {}
    labels = {}
    for i,v in enumerate(visuels):
        tree = visuels_tree
        spath = v['path'].split('.')
        for elt in spath[:-1]:
            if not elt in tree.keys():
                tree[elt] = {}
            tree = tree[elt]
            labels[elt] = vlabels.get(elt,elt)
        #if not v['domaine'] in visuels_tree.keys():
        #    visuels_tree[v['domaine']] = {}
        #    labels[v['domaine']] = domaines[v['domaine']]['nom']
        #if not v['visuel'] in visuels_tree[v['domaine']].keys():
        #    visuels_tree[v['domaine']][v['visuel']] = {}
        #    labels[v['visuel']] = v['nom']
        v['id'] = i
        v['leaf'] = True
        #visuels_tree[v['domaine']][v['visuel']] = v
        labels[spath[-1]] = v['nom']
        tree[spath[-1]] = v
        
    return dict(visuels_tree=visuels_tree,labels=labels, filtres_data=filtres_data)


def test():
    return dict(content=get_visuel_final(visuels[2]))

def test2():
    return BEAUTIFY(mdb.deputes.find_one())
    return BEAUTIFY(list(mdb.deputes.find({'$and':[{'depute_actif':True},{'stats.positions.exprimes':{'$lt':20}}]},{'stats.nbmots':1})))

def get_vdata(source,key,**args):
    if key=='depute_groupe':
        groupe_abrev = source['groupe_abrev']
        if groupe_abrev == 'NI':
            groupe_abrev = source['depute_election']['nuance']
            groupe_lib = nuances[groupe_abrev]
        else:
            groupe_lib = source['groupe_libelle'].split(':')[0].strip()
        depart = source['depute_departement_id'] if source['depute_departement_id'][0]!='0' else source['depute_departement_id'][1:]
        groupe = u"Député %s (%s) - %s" % (groupe_lib,groupe_abrev,depart)
        return groupe
    elif key=='depute_photo':
        path = os.path.join(request.folder, 'static/images/deputes/%s.jpg' % source['depute_id'])
        content = open(path).read()
        #content =requests.get('http://www2.assemblee-nationale.fr/static/tribun/15/photos/'+depute['depute_uid'][2:]+'.jpg').content
        photo = b64encode(content)
        return photo
    elif key=='depute_nom':
        return source['depute_hatvp'][0]['nom']
    elif key=='depute_prenom':
        return source['depute_hatvp'][0]['prenom']
    elif key=='depute_pctexprime':
        return ("%d%%" % round(source['stats']['positions']['exprimes'],0)).replace('.',',')
    elif key[:7]=='symbol_':
        symbol = key.split('_')[1]
        return XML(response.render('svg/symbols/%s.svg' % symbol, **args))

def getvisuel(name,key):
    visuel_def = visuels_defs[name]
    source = mdb[visuel_def['collection']].find_one({visuel_def['key']:key})
    params = {}
    for k,v in visuel_def['visuel_data'].iteritems():
        if isinstance(v,tuple):
            params[k] = get_vdata(source,v[0],**v[1])
        else:
            params[k] = get_vdata(source,v)
    svg = svgvisuel(visuel_def['visuel'],date=datetime.datetime.now().strftime('%d/%m/%Y'),**params)
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
    return dict(tweet=tweet,visuel=getvisuel('participationscrutins20',depute),id=depute,hasard=hasard)


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
    depute = mdb.deputes.find_one({'depute_shortid':id})
    data = getimage(id,w,h)
    r = api.request('statuses/update_with_media', {'status':'post'}, {'media': data})
    if r.status_code == 200:
        picurl = r.json()['extended_entities']['media'][0]['display_url']
        import urllib
        twitter = [ c['lien'] for c in depute['depute_contacts'] if c['type']=='twitter' ]
        twitter = twitter[0].split('/')[-2] if twitter else ''

        params = urllib.urlencode({'text':'---Votre message---   '+twitter+'   '+picurl})
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
        visuel = getvisuel('participationscrutins20',depid)
        data = str(visuel['data'])
        compl = ""
        ext = "svg"

    from cStringIO import StringIO
    response.headers['ContentType'] ="application/octet-stream";
    response.headers['Content-Disposition']="attachment; filename="+depid+compl+"."+ext

    return response.stream(StringIO(data),chunk_size=4096)
