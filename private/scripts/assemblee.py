#!/home/www-data/web2py/applications/observatoireassemblee/.pyenv/bin/python
# -*- coding: utf-8 -*-

import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

import scrapy
import requests
import json
import re
import datetime

import sys

output_path = sys.argv[1]

commlibs = {
u'Commission de la défense nationale et des forces armées':'OMC_PO59046',
u"Commission des affaires culturelles et de l'éducation":'OMC_PO419604',
u"Commission des lois constitutionnelles, de la législation et de l'administration générale de la République":'OMC_PO59051',
u'Commission des affaires étrangères':'OMC_PO59047',
u"Commission du développement durable et de l'aménagement du territoire":'OMC_PO419865',
u'Commission des affaires économiques':'OMC_PO419610',
u"Commission des finances, de l'économie générale et du contrôle budgétaire":'OMC_PO59048',
u'Commission des affaires sociales':'OMC_PO420120'
}

from scrapy.crawler import CrawlerProcess

import unicodedata
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
def normalize(s):
    return strip_accents(s).replace(u'\u2019','').replace('&apos;','').replace(u'\xa0','').encode('utf8').replace(' ','').replace("'",'').replace('-','').replace('\x0a','').replace('\xc5\x93','oe').decode('utf8').lower() if s else s


groupes = {}
commissions = {}
deputes = {}

class AssembleeSpider(scrapy.Spider):
    import requests
    import json
    import re
    import datetime
    name = "assemblee"
    noninscrits = "VIDE"
    base_url = 'http://www2.assemblee-nationale.fr'
    def start_requests(self):
        urls = [
         ('/instances/liste/groupes_politiques/effectif', self.parse_descgroupes),
         ('/instances/embed/41452/GP/instance/legislature/15', self.parse_groupes),
         ('/deputes/liste/clos',self.parse_deputesclos)]


        for url,callback in urls:
            request = scrapy.Request(url=self.base_url+url, callback=callback)
            yield request

    def parse_deputesclos(self,response):
        for dep in response.xpath('//table[contains(@class,"clos")]/tbody/tr'):
            link = dep.xpath('td/a/@href')[0].extract()
            cause = dep.xpath('td[3]/text()').extract()[0]
            request = scrapy.Request(url=self.base_url+link,callback=self.parse_depute)
            request.meta['cause'] = cause
            yield request

    def parse_descgroupes(self,response):
        for gp in response.xpath('//div[@id="deputes-list"]/div/div/table/tbody/tr'):
            infos = gp.xpath('td')[1]
            uid = infos.xpath('@data-omc')
            if not uid:
                continue
            uid = uid.extract()[0]
            abrev = infos.xpath('@id').extract()[0]
            libelle = infos.xpath('b/text()').extract()[0]
            if not uid in groupes.keys():
                groupes[uid] = dict()
            if abrev=='NI':
                AssembleeSpider.noninscrits = uid
            groupes[uid].update({'groupe_uid':uid,'groupe_abrev':abrev,'groupe_libelle':libelle})


    def parse_groupes(self,response):
        for gp in response.xpath('//li[@class="commission"]'):
            gp_nom = gp.xpath('div/h3/text()').extract()[0][7:]
            liens = gp.xpath('div/ul/li/a/@href')
            r = requests.get(self.base_url+liens[1].extract())
            gp_uid = re.search(r'data-uri-suffix="/instances/fiche/(OMC_PO[^/]+)',r.content).groups()[0]
            lien_decla = '/layout/set/ajax/content/view/embed/'+liens[2].extract().split('/')[-1] if len(liens)>2 else None
            lien_secre = '/layout/set/ajax/content/view/embed/'+liens[3].extract().split('/')[-1] if len(liens)>3 else None


            request = scrapy.Request(url=self.base_url+'/instances/tableau/%s/null/ajax/1/legislature/15' % gp_uid,callback=self.parse_groupe)
            request.meta['groupe_nom'] = gp_nom
            request.meta['groupe_uid'] = gp_uid.split('_')[1]
            request.meta['groupe_decla'] = requests.get(self.base_url + lien_decla).content if lien_decla else None
            #request.meta['groupe_declaration']
            yield request

    def parse_groupe(self,response):
        uid = response.meta['groupe_uid']
        if not uid in groupes.keys():
            groupes[uid] = dict()
        groupes[uid].update(dict(groupe_uid=uid,groupe_membres=[],groupe_declaration=response.meta['groupe_decla']))

        for m in response.xpath('//table[@class="instance"]/tbody/tr'):
            lien_dep = m.xpath('td/a/@href').extract()[0]
            sortname = m.xpath('td/@data-sort').extract()[0]
            dep_uid = lien_dep.split('/')[-1].split('_')[1]
            infos = m.xpath('td/text()').extract()
            qualite = infos[2].strip() or 'membre'
            commission = infos[3].strip()
            dep,circ = infos[4].strip().split('&nbsp')
            groupes[uid]['groupe_membres'].append(dict(uid=dep_uid,qualite=qualite))

            request = scrapy.Request(url=self.base_url+lien_dep,callback=self.parse_depute)
            request.meta['groupe'] = uid
            request.meta['groupe_qualite'] = qualite
            request.meta['dep'] = dep
            request.meta['circ'] = circ
            request.meta['sort_name'] = sortname.upper()
            yield request




    def parse_depute(self, response):
        import re
        import datetime
        nom = response.xpath('//div[contains(@class,"titre-bandeau-bleu")]/h1/text()').extract()[0].split('- ')[0]
        uid = response.url.split('_')[1]
        if not 'dep' in response.meta.keys():
            departement, circo = response.xpath('//dt[text()[contains(.,"Circonscription")]]/following-sibling::dd/ul/li/text()').extract()[0].split('&nbsp(')
        else:
            departement = response.meta['dep']
            circo = response.meta['circ']
        suppleant = response.xpath('//dt[text()[contains(.," Suppl")]]/following-sibling::dd/ul/li/text()')
        suppleant = suppleant[0].extract() if suppleant else None
        nais = response.xpath('//dt[text()[contains(.,"Biog")]]/following-sibling::dd/ul/li/text()')[0].extract()
        prof = response.xpath('//dt[text()[contains(.,"Biog")]]/following-sibling::dd/ul/li/text()')[1].extract().strip()
        ddn = re.search(r'le ([0-9]+[^0-9]+[0-9]+)',nais).groups()[0]
        ddn = datetime.datetime.strptime(ddn.replace('1er','1').encode('utf8'),'%d %B %Y')
        naissance = nais.strip().replace('/t','').replace('/n','')

        historique = []
        mandats = {}
        bureau = None
        # Fin mandat ?
        finmand = response.xpath('//dt[text()[contains(.,"fin de mandat")]]/following-sibling::dd/ul/li/text()')
        if finmand:
            finmand,finmand_cause = re.search(r'([0-9]+.+[0-9]+) \(([^)]+)\)',finmand[0].extract()).groups()
            #finmand_cause = response.meta['cause']
            place = None
            collaborateurs = None
            mand = None
            date_elec = None
            commissions = None
            debmand = None
            autres_mandats = None
            actif = False

        else:
            finmand = None
            finmand_cause = None
            actif = True
            # mandat
            mand = response.xpath('//h4[text()[contains(.,"Mandat")]]/following-sibling::ul/li/text()')[0].extract()
            date_elec,debmand = re.search(r'le ([^ ]+)[^:]+: ([^\)]+)',mand).groups()

            # historique commissions
            import datetime
            import re
            histo_com = {}
            hc = response.xpath('//div[@id="deputes-historique"]//span[@class="dt"]')

            for c in hc:
                nomcom = c.xpath('text()').extract()[0]
                histo_com[nomcom] = c.xpath('following-sibling::li')[0].xpath('ul/li/text()').extract()
                for h in histo_com[nomcom]:
                    debut,fin=re.search(r'du (\d+/\d+/\d+) au (\d+/\d+/\d+)',h).groups()
                    historique.append([datetime.datetime.strptime(debut,'%d/%m/%Y'),
                                       datetime.datetime.strptime(fin,'%d/%m/%Y'),
                                       commlibs.get(nomcom,nomcom)])

            historique.sort(reverse=True)
            historique = [(d.strftime('%d/%m/%Y'),f.strftime('%d/%m/%Y'),c) for d,f,c in historique]


            # commissions
            def getFctElts(elt):
                elts = response.xpath('//h4[text()[contains(.,"'+elt+'")]]/following-sibling::ul')
                _list = []
                if elts:
                    elts_quals = elts[0].xpath('span/text()').extract()
                    elts_ids = elts[0].xpath('li/ul/li/a')
                    if len(elts_quals)<len(elts_ids):
                        elts_quals = elts_quals*len(elts_ids)
                    for i,c in enumerate(elts_ids):
                        clink = self.base_url+c.xpath('@href').extract()[0]
                        clib = c.xpath('text()').extract()[0]
                        _list.append(dict(qualite=elts_quals[i],nom=clib,id=clink.split('_')[-1],lien=clink))
                return _list

            mandats['commissions'] = getFctElts('Commissions')
            mandats['delegations_bureau'] = getFctElts(u'du Bureau')
            mandats['delegations_office'] = getFctElts('et Office')

            autres_mandats = response.xpath('//div[@class="fonctions-tab-selection"]/div/div[@id="autres"]/ul/li/text()').extract()

            # bureau
            bur = response.xpath('//h4[text()[contains(.,"Bureau")]]/following-sibling::ul')
            if bur:
                bureau = bur[0].xpath('li/text()').extract()[0].replace('\t','').replace('\n','')
            # delegations


            place = response.xpath('//div[@id="hemicycle-container"]/@data-place').extract()[0]
            collaborateurs = response.xpath('//span[text()[contains(.,"collaborateurs")]]/parent::div/following-sibling::div/ul/li[contains(@class,"allpadding")]/text()').extract()

        contacts = []
        for c in response.xpath('//div[@id="deputes-contact"]//a[contains(@class,"url") or contains(@class,"email") or contains(@class,"facebook") or contains(@class,"twitter")]/@href').extract():
            if 'mailto' in c:
                contacts.append(dict(type='mail',lien=c))
            elif 'facebook' in c:
                contacts.append(dict(type='facebook',lien=c))
            elif 'twitter' in c:
                contacts.append(dict(type='twitter',lien=c))
            else:
                contacts.append(dict(type="site",lien=c))



        if 'groupe' in response.meta.keys():
            groupe = response.meta['groupe']
        else:
            groupe = response.xpath('//div[@id="deputes-illustration"]/span/a/@href').extract()
            if groupe:
                groupe = response.xpath('//div[@id="deputes-illustration"]/span/a/@href').extract()[0].split('/')[3].split('_')[1]
            else:
                groupe = None

        deputes[uid] = dict(
            depute_actif = actif,
            depute_nom = nom,
            depute_nom_tri = response.meta.get('sort_name',nom),
            depute_id = normalize(nom),
            depute_uid = uid,
            groupe_uid = groupe,
            groupe_qualite = response.meta.get('groupe_qualite','membre'),
            depute_departement = departement,
            depute_circo = circo,
            depute_suppleant = suppleant,
            depute_ddn = ddn.strftime('%d/%m/%Y'),
            depute_naissance = naissance,
            depute_dateelec = date_elec,
            depute_mandat_debut = debmand,
            depute_mandat_fin = finmand,
            depute_mandat_fin_cause = finmand_cause ,
            depute_bureau = bureau,
            depute_mandats = mandats,
            depute_profession = prof,
            depute_autresmandats = autres_mandats,
            depute_contacts = contacts,
            depute_place = place,
            depute_collaborateurs = collaborateurs,
            depute_commissions_historique = historique



            )

process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)','DOWNLOAD_DELAY':0.10
})


process.crawl(AssembleeSpider)
process.start() # the script will block here until the crawling is finished
import json
for d in deputes.values():
    if d['groupe_uid']==None:
        d['groupe_uid'] = AssembleeSpider.noninscrits
    g = groupes[d['groupe_uid']]
    d.update(dict(groupe_libelle=g['groupe_libelle'], groupe_abrev=g['groupe_abrev']))
with open(output_path+'/deputes.json','w') as f:
    f.write(json.dumps(deputes.values()))
with open(output_path+'/groupes.json','w') as f:
    f.write(json.dumps(groupes.values()))
