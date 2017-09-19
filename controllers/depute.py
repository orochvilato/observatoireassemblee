# -*- coding: utf-8 -*-
import random
import json
import datetime
import re

scrutins_by_id = cache.ram('scrutins_by_id',lambda: dict((s['scrutin_id'],s) for s in mdb.scrutins.find()), time_expire=0)
deputesFI = cache.ram('deputesFI',lambda: mdb.deputes.find({'groupe_abrev':'FI'}).distinct('depute_shortid'),time_expire=3600)
def index():
    shortid = request.args(0)
    depute = mdb.deputes.find_one({'depute_shortid':shortid}) or mdb.deputes.find_one({'depute_shortid':deputesFI[int(random.random()*len(deputesFI))]})
    
    votes = list(mdb.votes.find({'depute_uid':depute['depute_uid']}).sort('scrutin_num',-1))
    dates = {}
    for v in votes:
        sdat =  datetime.datetime.strptime(v['scrutin_date'],'%d/%m/%Y').strftime('%Y-%m-%d')
        if not sdat in dates.keys():
            dates[sdat] = {'e':0,'n':0}
        dates[sdat]['n']+= 1
        dates[sdat]['e']+= 1 if v['vote_position']!='absent' else 0
        
        
    return dict(dates=json.dumps(sorted([{"date": dat,"pct":round(float(v['e'])/v['n'],1)} for dat,v in dates.iteritems()],key=lambda x:x['date'])),**depute)

def ajax_votes():
    nb = 25
    page = int(request.args(0) or 2)-2
    depute_uid = request.vars.get('depute_uid',None);
    search = request.vars.get('search','').decode('utf8')
    skip = nb*page
    vote_filter = {'depute_uid':depute_uid}
    if not depute_uid:
        return ''
    if search:
        s_ids = []
        regx = re.compile(search, re.IGNORECASE)
        for s_id,s in scrutins_by_id.iteritems():
            repl = regx.subn('<high>'+search+'</high>',s['scrutin_desc'])
            if repl[1]:
                s['scrutin_desc'] = repl[0]
                s_ids.append(s_id)
        vote_filter['scrutin_id'] = {'$in':s_ids}
    votes = list(mdb.votes.find(vote_filter).sort('scrutin_num',-1).skip(skip).limit(nb))
    for v in votes:
        v.update(scrutins_by_id[v['scrutin_id']])
    return dict(votes=votes, next=(nb == len(votes)))

def ajax_itvs():
    nb = 25
    page = int(request.args(0) or 2)-2
    depute_uid = request.vars.get('depute_uid',None);
    search = request.vars.get('search','').decode('utf8')
    skip = nb*page
    itv_filter = {'depute_uid':depute_uid}
    if not depute_uid:
        return ''
    if search:
        regx = re.compile(search, re.IGNORECASE)
        itv_filter['itv_contenu_texte']=regx
    itvs = list(mdb.interventions.find(itv_filter).sort([('itv_date',-1),('itv_n',-1)]).skip(skip).limit(nb))
    if search:
        for itv in itvs:
            itv['itv_contenu']=regx.sub('<high>'+search+'</high>',itv['itv_contenu'])
    
    return dict(itvs=itvs, next=(nb == len(itvs)))
