# -*- coding: utf-8 -*-
# essayez quelque chose comme
import json
def updateElectionTour():
    mdb.deputes.update_one({'depute_shortid':'anneblanc'},{'$set':{'depute_election.adversaires':[{'nom':"M. André AT (retiré)",'voix':0}]}})
    mdb.deputes.update_many({'depute_election.adversaires.0': { "$exists": False } }, {'$set':{'depute_election.tour':1}})
    mdb.deputes.update_many({'depute_election.adversaires.0': { "$exists": True } }, {'$set':{'depute_election.tour':2}})
def test():
    return BEAUTIFY(mdb.interventions.find_one())
def error():
    1/0
def updateLogs():
    from geoip import geolite2
    import pycountry
    from user_agents import parse
    for l in mdb.logs.find({'$or':[{'geoip':None},{'agent_pretty':None}]}):
        match = geolite2.lookup(l['client'])
        pays = ""
        if match:
            country = match.country
            if country:
                pays = pycountry.countries.get(alpha_2=country).name
        agent_pretty = str(parse(l['agent']))
        mdb.logs.update({'_id':l['_id']},{'$set':{'geoip':pays,'agent_pretty':agent_pretty}})

def logs():
    updateLogs()
    return dict(logs=mdb.logs.find().sort('date',-1).limit(200))
