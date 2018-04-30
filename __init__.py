from mycroft import FallbackSkill, intent_file_handler, intent_handler
from adapt.intent import IntentBuilder
import requests
import json
from bs4 import BeautifulSoup

__author__ = "jarbasAI"


class AskTheCatterpillarSkill(FallbackSkill):
    def __init__(self):
        super(AskTheCatterpillarSkill, self).__init__()
        self.substance_list = self.get_substance_list()
        self.drug_slang = {u'benzo fury': u'6-apb', u'l': u'lsd', u'x': u'mdma', u'speed': u'amphetamine', u'pepper oil': u'capsaicin', u'cpp': u'piperazines', u'blow': u'cocaine', u'foxy': u'5-meo-dipt', u'symmetry': u'salvinorin b ethoxymethyl ether', u' nexus': u'2c-b', u' tea': u'caffeine', u'robo': u'dxm', u' tussin': u'dxm', u'methylethyltryptamine': u'met', u'it-290': u'amt', u'jwh-018': u'cannabinoids', u'coffee': u'caffeine', u'mpa': u'methiopropamine', u' ergine': u'lsa', u' harmine': u'harmala', u'mxe': u'methoxetamine', u'4-ho-met; metocin; methylcybin': u'4-hydroxy-met', u' mdea': u'mde', u'elavil': u'amitriptyline', u'bk-mdma': u'methylone', u'eve': u'mde', u' a2': u'piperazines', u'dimitri': u'dmt', u'plant food': u'mdpv', u' dr. bob': u'dob', u'mini thins': u'ephedrine', u'meth': u'methamphetamines', u'acid': u'lsd', u' etc.': u'nbome', u' wine': u'alcohol', u'toad venom': u'bufotenin', u' methyl-j': u'mbdb', u'krokodil': u'desomorphine', u' 5-hydroxy-dmt': u'bufotenin', u' 3-cpp': u'mcpp', u'various': u'other chemicals', u' special k': u'ketamine', u' ice': u'methamphetamines', u' nrg-1': u'mdpv', u' gravel': u'alpha-pvp', u'whippits': u'nitrous', u'g': u'ghb', u'k': u'ketamine', u' harmaline': u'harmala', u'bob': u'dob', u'4-ace': u'4-acetoxy-dipt', u'quaaludes': u'methaqualone', u' opium': u'opiates', u'u4ea': u'4-methylaminorex', u' meopp': u'piperazines', u'methcathinone': u'cathinone', u'horse': u'heroin', u'haoma': u'harmala', u'unknown': u'"spice" product', u'4-b': u'1,4-butanediol', u'naptha': u'petroleum ether', u'beer': u'alcohol', u'bees': u'2c-b', u'2c-bromo-fly': u'2c-b-fly', u'flatliner': u'4-mta', u'orexins': u'hypocretin', u"meduna's mixture": u'carbogen', u' bdo': u'1,4-butanediol', u'fatal meperedine-analog contaminant': u'mptp', u'piperazine': u'bzp', u'4-ma': u'pma', u' paramethoxyamphetamine': u'pma', u'eden': u'mbdb', u'theobromine': u'chocolate', u' la-111': u'lsa', u' lysergamide': u'lsa', u' yaba': u'methamphetamines', u'ethyl cat': u'ethylcathinone', u'stp': u'dom', u'2c-c-nbome': u'nbome', u' morphine': u'opiates', u'flakka': u'alpha-pvp', u'yage': u'ayahuasca', u'ecstasy': u'mdma', u' ludes': u'methaqualone', u' goldeneagle': u'4-mta', u'4-mma': u'pmma', u'o-dms': u'5-meo-amt', u' liquor': u'alcohol', u'mephedrone': u'4-methylmethcathinone', u'1': u'1,4-butanediol', u'phencyclidine': u'pcp', u' crystal': u'methamphetamines', u'pink adrenaline': u'adrenochrome', u'4-mec': u'4-methylethcathinone', u'green fairy': u'absinthe', u'laa': u'lsa', u' cp 47': u'cannabinoids', u' paramethoxymethylamphetamine': u'pmma', u'5-meo': u'5-meo-dmt', u'alpha': u'5-meo-amt', u'mescaline-nbome': u'nbome', u'25c-nbome': u'2c-c-nbome', u'flephedrone': u'4-fluoromethcathinone', u'bzp': u'piperazines', u'codeine': u'opiates', u'foxy methoxy': u'5-meo-dipt', u'25i-nbome': u'2c-i-nbome', u'3c-bromo-dragonfly': u'bromo-dragonfly', u'mdai': u'mdai', u' tfmpp': u'piperazines'}

    def initialize(self):
        self.register_fallback(self.handle_fallback, 50)

    @staticmethod
    def get_substance_list():
        base_url = "https://psychonautwiki.org/wiki/Summary_index"
        response = requests.get(base_url).text
        soup = BeautifulSoup(response, "lxml")

        table = soup.findAll('div', {'class': 'panel radius'})
        substances = []
        for panel in table:
            subs = panel.find_all("li", {"class": "featured list-item"})
            for s in subs:
                subcat = s.find("span", {"class": "mw-headline"})
                i = 0
                if subcat is not None:
                    subcat = subcat.getText()
                s = s.find_all("a")
                if subcat is not None and s[0].getText() == subcat:
                    i = 1
                for substance in s[i:]:
                    sub_name = substance.getText().replace("/Summary", "").replace("(page does not exist)", "").strip()
                    substances.append(sub_name)
        return substances

    def is_drug(self, utterance):

        # check for drug slang names
        for substance in self.drug_slang:
            substance = self.drug_slang[substance].strip()
            if substance.lower() in utterance.split(" "):
                return utterance.replace(substance.lower(), substance)

        # check substance list
        for substance in self.substance_list:
            if substance.lower() in utterance.split(" "):
                return utterance.replace(substance.lower(), substance)

        # probably not talking about drugs
        return False

    def handle_fallback(self, message):
        utterance = message.data.get("utterance", "").lower()
        utterance = self.is_drug(utterance)
        if utterance:
            self.speak(self.ask_the_caterpillar(utterance))
            return True
        return False

    @intent_handler(IntentBuilder('WhatisHarmReduction').require('What').require('HarmReduction'))
    def handle_what_HR(self, message):
        self.speak_dialog("what_harm_reduction")

    @intent_handler(IntentBuilder('WhatisAskCaterpillar').require('What').require('AskTheCaterpillar'))
    def handle_what_caterpillar(self, message):
        self.speak_dialog("what_caterpillar")

    @intent_handler(IntentBuilder('AskCaterpillar').require('AskTheCaterpillar'))
    def handle_ask_caterpillar(self, message):
        query = message.utterance_remainder()
        self.speak(self.ask_the_caterpillar(query))

    @staticmethod
    def ask_the_caterpillar(query="what is lsd"):
        data = requests.post('https://www.askthecaterpillar.com/query', {"query": query})
        data = json.loads(data.text)
        return data["data"]["messages"][0]["content"]


def create_skill():
    return AskTheCatterpillarSkill()

