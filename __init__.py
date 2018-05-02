from mycroft import FallbackSkill, intent_file_handler, intent_handler
from mycroft.util.parse import match_one
from mycroft.util.log import LOG
from adapt.intent import IntentBuilder
from pysychonaut import AskTheCaterpillar, Erowid, PsychonautWiki
import random

__author__ = "jarbasAI"


class AskTheCaterpillarSkill(FallbackSkill):
    def __init__(self):
        super(AskTheCaterpillarSkill, self).__init__()
        self.caterpillar = AskTheCaterpillar()
        self.wiki = PsychonautWiki()
        self.chemicals = {}
        self.plants = {}
        self.animals = {}
        self.smarts = {}
        self.herbs = {}
        self.pharms = {}
        self.substances = []
        self.categories = {}
        self.populate_substance_entries()

    def parse_substance(self, text):
        data = {}
        # correct drug name slang
        sub = self.caterpillar.fix_substance_names(text)
        if not sub:
            LOG.warn("probable bad substance name")
        else:
            text = sub

        # match drug to info
        best, score = match_one(text, self.substances)
        LOG.debug(str(score) + " " + best)
        if best in self.chemicals.keys():
            data = self.chemicals[best]
        elif best in self.plants.keys():
            data = self.plants[best]
        elif best in self.animals.keys():
            data = self.animals[best]
        elif best in self.herbs.keys():
            data = self.herbs[best]
        elif best in self.pharms.keys():
            data = self.pharms[best]

        if data is None or score < 0.5:
            return False
        self.set_context("url", data["url"])
        self.set_context("substance", data["name"])
        LOG.info(str(data))
        return data

    def populate_substance_entries(self):
        for chem in Erowid.get_chemicals():
            self.chemicals[chem["name"]] = chem
        self.substances += self.chemicals.keys()

        for animal in Erowid.get_animals():
            self.animals[animal["name"]] = animal
        self.substances += self.animals.keys()

        for smart in Erowid.get_smarts():
            self.smarts[smart["name"]] = smart
        self.substances += self.smarts.keys()

        for plant in Erowid.get_plants():
            self.plants[plant["name"]] = plant
        self.substances += self.plants.keys()

        for herb in Erowid.get_herbs():
            self.herbs[herb["name"]] = herb
        self.substances += self.herbs.keys()

        for pharm in Erowid.get_pharms():
            self.pharms[pharm["name"]] = pharm
        self.substances += self.pharms.keys()

        for key in self.wiki.substances.keys():
            self.categories[key] = []
            for sub_cat in self.wiki.substances[key]:
                self.categories[sub_cat] = []
                for substance in self.categories[sub_cat]:
                    self.categories[key].append(substance)
                    self.categories[sub_cat].append(substance)

    def speak_report(self, trip_report):
        report_id = trip_report["exp_id"]
        report = Erowid.get_experience(report_id)
        LOG.info(str(report))
        self.set_context("url", trip_report["url"])
        self.set_context("substance", trip_report["substance"])
        self.speak(report["name"])
        self.speak_dialog("trip_report", {"substance": trip_report["substance"]})
        # TODO split speech in chunks for better TTS
        self.speak(report["experience"])

    def initialize(self):
        # register generic fallback for drug questions
        self.register_fallback(self.handle_fallback, 50)

        # generate vocabulary for substances
        for categorie in self.categories:
            self.register_vocabulary(categorie.lower(), "categorie")

        # info - tell me about drug_name
        # trip report - describe a drug_name experience
        for substance in self.substances:
            self.register_vocabulary(substance.lower(), "substance")
        for substance in self.caterpillar.drug_slang.keys():
            self.register_vocabulary(substance.lower(), "substance")
        for substance in self.caterpillar.substance_list:
            self.register_vocabulary(substance.lower(), "substance")
        for key in self.caterpillar.drug_slang:
            substance = self.caterpillar.drug_slang[key]
            self.register_vocabulary(substance.lower(), "substance")

    def handle_fallback(self, message):
        utterance = message.data.get("utterance", "").lower()
        utterance = self.caterpillar.fix_substance_names(utterance)
        if utterance:
            self.speak(self.caterpillar.ask_the_caterpillar(utterance))
            substance = self.wiki.extract_substance_name(utterance)
            if substance:
                self.set_context("substance", substance)
            return True
        return False

    @intent_handler(IntentBuilder("MoreSubstanceInfo").require("more").require("substance"))
    def handle_more_substance_info(self, message):
        substance = message.data["substance"]

        data = self.parse_substance(substance)

        if not data:
            self.speak_dialog("bad_drug")
            return

        url = data["url"]
        data = Erowid.parse_page(url)
        self.speak(data["description"])

    @intent_handler(IntentBuilder("SubstanceInfo").require("what").require("substance"))
    def handle_substance_info(self, message):
        substance = message.data["substance"]

        data = self.parse_substance(substance)

        if not data:
            self.speak_dialog("bad_drug")
            return

        self.speak_dialog("substance_info",
                          {"substance": data["name"],
                           "other_names": data["other_names"],
                           "effects": data["effects"]})

    @intent_handler(IntentBuilder("TripReport").require("trip_report").require("substance").optionally("categorie"))
    def handle_search_trip_report(self, message):
        if message.data.get("categorie"):
            substance = random.choice(self.categories[message.data["categorie"]])
        else:
            substance = message.data["substance"]
        sub = self.wiki.extract_substance_name(substance)
        if sub is None:
            self.log.warn("probable bad substance name")
        else:
            substance = sub
        reports = Erowid.search_reports(substance)
        report = random.choice(reports)
        self.speak_report(report)

    @intent_handler(IntentBuilder('RandomTripReport').require('random').require('trip_report'))
    def handle_random_trip_report(self, message):
        trip_report = Erowid.random_experience()
        self.speak_report(trip_report)

    @intent_handler(IntentBuilder('WhatisErowid').require('What').require('Erowid'))
    def handle_what_erowid(self, message):
        self.speak_dialog("what_erowid")

    @intent_handler(IntentBuilder('ErowidMission').optionally('What').require('Erowid').require("mission"))
    def handle_mission_erowid(self, message):
        self.speak_dialog("erowid_mission")

    @intent_handler(IntentBuilder('WhatisHarmReduction').require('What').require('HarmReduction'))
    def handle_what_HR(self, message):
        self.speak_dialog("what_harm_reduction")

    @intent_handler(IntentBuilder('WhatisAskCaterpillar').require('What').require('AskTheCaterpillar'))
    @intent_handler(IntentBuilder('WhatisAskCaterpillar2').optionally('What').require('AskTheCaterpillar').require("mission"))
    def handle_what_caterpillar(self, message):
        self.speak_dialog("what_caterpillar")

    @intent_handler(IntentBuilder('AskCaterpillar').require('AskTheCaterpillar'))
    def handle_ask_caterpillar(self, message):
        query = message.utterance_remainder()
        self.speak(self.caterpillar.ask_the_caterpillar(query))
        substance = self.wiki.extract_substance_name(query)
        if substance:
            self.set_context("substance", substance)


def create_skill():
    return AskTheCaterpillarSkill()

