# -*- coding: utf-8 -*-
# essayez quelque chose comme
import re
import json

mdb = client.obsass

from collections import OrderedDict
tri_choices = OrderedDict([('stats.positions.exprimes',{'label':'Participation','classe':'deputes-participation','rank':'exprimes','precision':0,'unit':'%'}),
            ('stats.positions.dissidence',{'label':'Contre son groupe','classe':'deputes-dissidence','rank':'dissidence','precision':0,'unit':'%'}),
            ('stats.compat.FI',{'label':'Vote Insoumis','classe':'deputes-fi','rank':'compatFI','precision':0,'unit':'%'}),
            ('stats.compat.REM',{'label':'Vote En marche','classe':'deputes-em','rank':'compatREM','precision':0,'unit':'%'}),
            ('stats.nbitvs',{'label':"Nombre d'interventions",'classe':'deputes-interventions','rank':'nbitvs','precision':0,'unit':''}),
            ('stats.nbmots',{'label':"Nombre de mots",'classe':'deputes-mots','rank':'nbmots','precision':0,'unit':''}),
            ('stats.election.inscrits',{'label':"Voix en % des inscrits",'classe':'deputes-pctinscrits','precision':2,'rank':'pctinscrits','unit':'%'}),
            ('stats.election.exprimes',{'label':"Voix en % des votes exprimés",'classe':'deputes-pctexprimes','precision':2,'rank':'pctexprimes','unit':'%'}),
            ('depute_nom_tri',{'label':"Nom",'classe':'','rank':'N/A','unit':''})
            ])
tri_items = {'tops': ('stats.positions.exprimes','stats.positions.dissidence','stats.compat.FI','stats.compat.REM','stats.nbitvs','stats.nbmots','stats.election.exprimes','stats.election.inscrits'),
             'liste': ('depute_nom_tri','stats.positions.exprimes','stats.positions.dissidence','stats.compat.FI','stats.compat.REM')}    
top_choices = [('top','Top'),
            ('flop','Flop'),
            ]

# cache
CACHE_EXPIRE = 3600
cache_groupes = cache.disk('groupes', lambda: [(g['groupe_abrev'],g['groupe_libelle']) for g in mdb.groupes.find()], time_expire=CACHE_EXPIRE)
cache_regions = cache.disk('regions',lambda: sorted([(r,r) for r in mdb.deputes.distinct('depute_region')],key=lambda x:x), time_expire=CACHE_EXPIRE)
cache_ages = cache.disk('ages',lambda: sorted([(a,a) for a in mdb.deputes.distinct('depute_classeage')],key=lambda x:x), time_expire=CACHE_EXPIRE)
cache_csp = cache.disk('csp',lambda: sorted([(c,c) for c in mdb.deputes.distinct('depute_csp')],key=lambda x:x), time_expire=CACHE_EXPIRE)
# ---------------------------------
# Page députés
# ---------------------------------

def index():
    redirect(URL('liste'))

def liste():
    
    params = dict(request.vars)
    return dict(params=params,tris=tri_choices,tri_items=tri_items['liste'],groupes = cache_groupes,regions = cache_regions, csp=cache_csp, ages=cache_ages)


def ajax_liste():
    return _ajax('liste')

def tops():
    params = dict(request.vars)
    params['top'] = params.get('top','top')

    return dict(params=params,tops=top_choices,tris=tri_choices, tri_items=tri_items['tops'],groupes = cache_groupes,regions = cache_regions)
def ajax_top():
    return _ajax('tops')


def _ajax(type_page):
    # ajouter des index (aux differentes collections)
    nb = 25
    count = request.vars.get('count',None)
    age = request.vars.get('age',None)
    csp = request.vars.get('csp',None)
    page = int(request.args(0) or 2)-2
    groupe = request.vars.get('gp',None)
    direction = int(request.vars.get('di',1))
    text = request.vars.get('txt','').decode('utf8')
    region = request.vars.get('rg',None)
    top = request.vars.get('top',None)
    tri = request.vars.get('tri','stats.positions.exprimes' if top else 'depute_nom_tri')
    if (count):
        filters = []
        if groupe:
            filters.append(groupe)
        if csp:
            filters.append(csp)
        if region:
            filters.append(region)
        if age:
            filters.append(age)
        if top:
            filters.append(tri_choices[tri]['rank'])
        obsass_log((top if top else 'liste')+'_depute',filters)
        
    tops_dir = {'stats.positions.exprimes':-1,
                  'stats.positions.dissidence':-1,
                  'stats.nbitvs':-1,
                  'stats.nbmots':-1,
                  'stats.compat.FI':-1,
                  'stats.compat.REM':-1,
                  'stats.election.exprimes':-1,
                  'stats.election.inscrits':-1}

    filter = {'$and':[ {'depute_actif':True}]}

    if csp:
        filter['$and'].append({'depute_csp':csp})
    if age:
        filter['$and'].append({'depute_classeage':age})
    if groupe:
        filter['$and'].append({'groupe_abrev':groupe})
    if region:
        filter['$and'].append({'depute_region':region})
    if text:
        regx = re.compile(text, re.IGNORECASE)
        filter['$and'].append({'depute_nom':regx})

    sort = []
    if top:
        direction = tops_dir[tri] * (1 if top=='top' else -1)
        rank = 'stats.ranks.'+('down' if (tops_dir[tri]==-1 and top=='top') else 'up')+'.'+tri_choices[tri]['rank']
        #sort += [ ('stats.nonclasse',1),(tri,direction),(rank,tops_dir[tri]*(-1 if top=='top' else 1))]
        sort += [ ('stats.nonclasse',1),(rank,1)]
        filter['$and'].append({tri:{'$ne':None}})
    else:
        sort += [ (tri,direction)]

    skip = nb*page
    mreq = mdb.deputes.find(filter).sort(sort)
    if count:
        rcount = mreq.count()
        compl = ""
        if top:
            filter['$and'][-1] = {tri:{'$eq':None}}
            excount = mdb.deputes.find(filter).sort(sort).count()
            if excount>0 and tri in ('stats.compat.FI','stats.compat.REM'):
                compl="(%d députés non pris en compte car leur participation est inférieure a %d %%)" % (excount,seuil_compat)
        
        return json.dumps(dict(count=rcount,compl=compl))
    
    deputes = list(mreq.skip(skip).limit(nb))

    return dict(deputes=deputes, count=count,tri = tri, top=tri_choices[tri], top_dir=('down' if (tops_dir.get(tri,0)==-1 and top=='top') else 'up'),tf=top, skip = skip, next=(nb == len(deputes) ))

def comparer():
    depids = request.args
    items_selection = ['stats.positions.exprimes','stats.nbmots','stats.nbitvs','stats.election.exprimes','stats.election.inscrits']
    deputes = list(mdb.deputes.find({'depute_shortid':{'$in':depids}}))
    items_pos = {}
    for k,it in tri_choices.iteritems():
        items_pos[k] = sorted([ (i,getdot(d,k)) for i,d in enumerate(deputes) ],key=lambda x:x[1], reverse=True)
    votes = dict((k,{}) for k in scrutins_cles.keys())
    for v in mdb.votes.find({'$and':[{'depute_uid':{'$in':[d['depute_uid'] for d in deputes]}},{'scrutin_num':{'$in':scrutins_cles.keys()}}]}):
        votes[v['scrutin_num']][v['depute_uid']] = v['vote_position']
    obsass_log('comparer',request.args)
    return dict(deputes=deputes,items_pos=items_pos,votes=votes,items=tri_choices,items_selection=items_selection)
