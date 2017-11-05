# -*- coding: utf-8 -*-
# essayez quelque chose comme
deputefields = ['depute_uid','depute_id','depute_shortid','depute_region','depute_departement','depute_departement_id',
                'depute_circo','depute_nom','depute_contacts','groupe_abrev','groupe_libelle',
                'depute_election','depute_profession','depute_naissance','depute_suppleant',
                'depute_actif','depute_mandat_debut','depute_mandat_fin','depute_mandat_fin_cause',
                'depute_bureau','depute_mandats','depute_autresmandats','depute_collaborateurs',
                'depute_hatvp','depute_nuages','depute_place','stats']


def get():
    funct = request.args(0)
    if not funct in ['depute','groupe']:
        return
    if funct=='depute':
        result=getDepute()

    from bson import json_util
    response.headers['Content-Type'] = 'text/json'
    return json_util.dumps(result)

def getDepute():
    shortid = request.args(1)
    mfields = dict((f,1) for f in deputefields)
    mfields.update({'_id':False})
    depute = mdb.deputes.find_one({'depute_shortid':shortid},mfields)
    if not depute:
        depute = mdb.deputes.find_one({'depute_shortid':deputesFI[int(random.random()*len(deputesFI))]},mfields)
    else:
        obsass_log('fiche',shortid)

       
    photo_an='http://www2.assemblee-nationale.fr/static/tribun/15/photos/'+depute['depute_uid'][2:]+'.jpg'
    depnumdep = depute['depute_departement_id'][1:] if depute['depute_departement_id'][0]=='0' else depute['depute_departement_id']
    depute_circo_complet = "%s / %s (%s) / %se circ" % (depute['depute_region'],depute['depute_departement'],depnumdep,depute['depute_circo'])

    votes = list(mdb.votes.find({'depute_uid':depute['depute_uid']}).sort('scrutin_num',-1))
    votes_cles = list(mdb.votes.find({'depute_uid':depute['depute_uid'],'scrutin_num':{'$in':scrutins_cles.keys()}},{'scrutin_num':1,'vote_position':1,'scrutin_dossierLibelle':1}).sort('scrutin_num',-1))
    from collections import OrderedDict
    s_cles = OrderedDict()
    for v in votes_cles:
        v.update(scrutins_cles[v['scrutin_num']])
        if not v['theme'] in s_cles:
            s_cles[v['theme']] = []
        s_cles[v['theme']].append(v)
    dates = {}
    weeks = {}
    for v in votes:
        pdat =  datetime.datetime.strptime(v['scrutin_date'],'%d/%m/%Y')
        wdat = pdat.strftime('%Y-S%W')
        sdat = pdat.strftime('%Y-%m-%d')
        if not wdat in weeks.keys():
            weeks[wdat] = {'e':0,'n':0}

        if not sdat in dates.keys():
            dates[sdat] = {'e':0,'n':0}
        weeks[wdat]['n']+= 1
        dates[sdat]['n']+= 1
        weeks[wdat]['e']+= 1 if v['vote_position']!='absent' else 0
        dates[sdat]['e']+= 1 if v['vote_position']!='absent' else 0

    
    resp = dict(dates=sorted([{"date": dat,"pct":round(float(v['e'])/v['n'],3)} for dat,v in dates.iteritems()],key=lambda x:x['date']),
                weeks=sorted([{"week": w,"pct":100*round(float(v['e'])/v['n'],2)} for w,v in weeks.iteritems()],key=lambda x:x['week']),
                votes_cles=s_cles,
                depute_circo_complet = depute_circo_complet,
                depute_photoan = photo_an,
                id = depute['depute_shortid'],
                **depute)
    
    return resp
