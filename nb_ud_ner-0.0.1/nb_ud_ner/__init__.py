# coding: utf8
from __future__ import unicode_literals

from pathlib import Path
from spacy.util import load_model_from_init_py, get_model_meta
from spacy.language import Language
from spacy.tokens import Span
from spacy.matcher import PhraseMatcher
from spacy.matcher import Matcher
import ujson
import os.path
from collections import defaultdict
import string
import re
import glob

__version__ = get_model_meta(Path(__file__).parent)['version']


def load(**overrides):
    Language.factories['entity_matcher'] = lambda nlp, **cfg: EntityMatcher(nlp, **cfg)
    return load_model_from_init_py(__file__, **overrides)

class EntityMatcher(object):
    name = 'entity_matcher'  # component name shown in pipeline

    def __init__(self, nlp):
        patterns = defaultdict(list)
        Span.set_extension('via_patterns', default=False)
        labels = ['LOC', 'PER', 'ORG', 'MISC']
        self.matcher = PhraseMatcher(nlp.vocab)
        #get entities with given label and add to matcher for each label in list
        for label in labels:
            self.entities = self.get_entities(label)
            patterns[label] = [nlp(text) for text in self.entities]

        for label, pattern in patterns.items():
            self.matcher.add(label, None,  *pattern)
        
    def __call__(self, doc):
        matches = self.matcher(doc)
        spans = []  # keep the spans for later so we can merge them afterwards
        for label_id, start, end in matches:
            # create Span for matched entity and assign label
            entity = Span(doc, start, end, label=label_id)
            entity._.via_patterns = True
            spans.append(entity)
            token_lemma = ""
            for token in doc[start:end]:
                if token_lemma == "":
                    token_lemma = token.lemma_
                else:
                    token_lemma = token_lemma + " " + token.lemma_

            #can't force pos_, because pos_ is decided from tag_ 
            #force tag_ to be PROPN, all named entities are PROPN, otherwise 'Hvaler' will be NOUN 
            #lemma will be overwritten when setting token's tag, so I have to overwrite it with the correct form again
            for token in doc[start:end]:
                token.tag_ = 'PROPN___'
                token.lemma_ = token_lemma.lower()
            
        doc.ents = list(doc.ents) + spans  # overwrite doc.ents and add entities – don't replace!
        for span in spans:
            #print(span)
            span.merge()  # merge all spans at the end to avoid mismatched indices
        return doc  # don't forget to return the Doc!

    def get_entities(self, label):
        entity_list = []
        #get directory of this script
        script_dir = os.path.dirname(__file__)
        #find all .csv files in this directory's entity_matcher folder
        path = glob.glob(script_dir + '/entity_matcher/*csv')
        for filename in path:
            filename2 = re.match('.*?entity_matcher/(\w+).csv', filename)
            if filename2 != None:
                file_label = filename2.group(1)
                #find out which files contain entities with the label we are looking for
                if label.lower() in file_label:
                    first_line_skipped = False
                    #column in csv file to read from
                    columns = []
                    encoding = 'utf-8'
                    if label == 'LOC':
                        encoding = 'latin-1'
                    with open(filename, 'r', encoding=encoding) as file:
                        for line in file:
                            line = line.split(";")
                            #skip the first line containg heading etc
                            if not first_line_skipped:
                                columns = self.find_column_in_file(columns, line)
                                first_line_skipped = True
                                continue
                            for column in columns:
                                entity = self.do_string_preprocessing(line[column], label)
                                entity_list = self.add_new_entities_to_list(entity, file_label, entity_list)

        return entity_list

    def add_new_entities_to_list(self, entity, file_label, entity_list):
        words = entity.split()
        #PhraseMatcher only supports phrases up to 10 tokens
        #don't add duplicates
        #don't allow empty tokens, it throws ValueError: [T001] Max length currently 10 for phrase matching
        if len(words) < 10 and entity.title() not in entity_list and entity != "":
            #the cities' names with / in this file have to be split in 2 separate entities
            if file_label == 'tettsteder_loc' and '/' in entity:
                entities = entity.split('/')
                for e in entities:
                    entity_list.append(e.title())
            else:
                entity_list.append(entity.title())
        return entity_list

    def find_column_in_file(self, columns, line):
        cat_counter = 0
        #find out which columns contain names
        for cat in line:
            cat = cat.lower().strip("\"")
            if cat == 'navn' or cat == 'name' or cat == 'shortname' or cat == 'tettsted' or cat == 'kommune':
                columns.append(cat_counter)
            cat_counter += 1
        return columns

    def do_string_preprocessing(self, name, label):
        #only remove digits from names and locations, we want to keep them for organizations etc 
        #keep - / and . in locations and names (U.S.A., Bosnia-Hercegovina, Trinid/Tobago)
        if label != 'ORG' or label != 'MISC':
            entity = re.sub(r'[^\w\s/-/.]','',name)
            #entity = re.sub(r'[\d\s]','',entity)
            entity = re.sub(r'[\d]','',entity)
            #only remove whitespace at the beginning
            entity = re.sub(r'^[\s]','',entity)
            entity = re.sub(r'$[\s]','',entity)
        else:
            #remove punctuation etc
            entity = re.sub(r'[^\w\s]','',name)
        if label == 'LOC':
            #print(entity)
            entity = re.sub(r'i alt','',entity)
        #remove extra whitespace after removing punctuation, otherwise it will end up as a token
        entity = re.sub(' +',' ',entity)
        return entity