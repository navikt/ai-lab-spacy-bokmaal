# coding: utf8
from __future__ import unicode_literals

from pathlib import Path
from spacy.util import load_model_from_init_py, get_model_meta
from spacy.language import Language
from spacy.tokens import Span
from spacy.matcher import PhraseMatcher
from spacy.matcher import Matcher
import spacy
import ujson
import os.path
from collections import defaultdict
import string
import re
import glob
import pandas as pd
import csv


__version__ = get_model_meta(Path(__file__).parent)['version']


def load(**overrides):
    Language.factories['entity_matcher'] = lambda nlp, **cfg: EntityMatcher(nlp, **cfg)
    return load_model_from_init_py(__file__, **overrides)

class EntityMatcher(object):
    name = 'entity_matcher'  # component name shown in pipeline

    def __init__(self, nlp: Language):
        patterns = defaultdict(list)
        Span.set_extension('via_patterns', default=False)
        self.matcher = PhraseMatcher(nlp.vocab)
        #get entities with given label and add to matcher for each label in list
        self.entities = self.get_entities()
        entity_dict = self.entities.to_dict('index')
        for row, dictionary in entity_dict.items():
            label = dictionary['label']
            name = dictionary['name']
            name = nlp(name)
            self.matcher.add(label, None, name)
    
    def __call__(self, doc: spacy.tokens.doc.Doc):
        matches = self.matcher(doc)
        spans = []  # keep the spans for later so we can merge them afterwards
        for label_id, start, end in matches:
            # create Span for matched entity and assign label
            entity = Span(doc, start, end, label=label_id)
            entity._.via_patterns = True
            print("entity: ")
            #that's a string
            print(entity.text)
            #print("start: " + str(start) + ", end: " + str(end))
            spans.append(entity)
            print("tokens in that entity: ")
            token_lemma = ""
            for token in doc[start:end]:
                print(token)
                if token_lemma == "":
                    token_lemma = token.lemma_
                else:
                    token_lemma = token_lemma + " " + token.lemma_
            
            #can't force pos_, because pos_ is decided from tag_ 
            #force tag_ to be PROPN, all named entities are PROPN, otherwise 'Hvaler' will be NOUN 
            #lemma will be overwritten when setting token's tag, so I have to overwrite it with the correct form again
            for token in doc[start:end]:
                #token.ent_type_ = "PErgs"
                token.tag_ = 'PROPN___'
                token.lemma_ = token_lemma.lower()
            print("")
        doc.ents = list(doc.ents) + spans  # overwrite doc.ents and add entities – don't replace!
        for span in spans:
            span.merge()  # merge all spans at the end to avoid mismatched indices
        return doc  # don't forget to return the Doc!
    
    def get_entities(self):
        entity_dict = {}
        #get directory of this script
        script_dir = os.path.dirname(__file__)
        #print(script_dir)
        #find all .csv files in this directory's entity_matcher folder
        #should be only one file now
        path = glob.glob(script_dir + '/entity_matcher/*csv')
        #print(label)
        for filename in path:
            print(filename)
            filename2 = re.match('.*?entity_matcher/(\w+).csv', filename)
            if filename2 != None:
                df = self.load_dataframe(filename, encoding='utf-8')
                #print("dataframe")
                return df

    def load_dataframe(self, uri_to_file: str, encoding: str):
        #print(uri_to_file)
        path = Path(uri_to_file)
        #print(path)
        try:
            return pd.read_csv(path.absolute(), sep=";", encoding=encoding, quoting=csv.QUOTE_NONE, index_col=0)
        except pd.errors.EmptyDataError as err:
            print(err)

