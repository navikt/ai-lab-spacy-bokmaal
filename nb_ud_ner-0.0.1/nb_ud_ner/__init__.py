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
        doc.ents = list(doc.ents) + spans  # overwrite doc.ents and add entities – don't replace!
        for span in spans:
            span.merge()  # merge all spans at the end to avoid mismatched indices
        return doc  # don't forget to return the Doc!

    def get_entities(self, label):
        entity_list = []
        #get directory of this script
        script_dir = os.path.dirname(__file__)
        #find all .csv files in this directory's entity_matcher folder
        path = glob.glob(script_dir + '/entity_matcher/*csv')
        print(label)
        for filename in path:
            filename2 = re.match('.*?entity_matcher/(\w+).csv', filename)
            if filename2 != None:
                file_label = filename2.group(1)
                #find out which files contain entities with the label we are looking for
                if label.lower() in file_label:
                    first_line_skipped = False
                    #column in csv file to read from
                    column = 0
                    encoding = 'utf-8'
                    if label == 'LOC':
                        encoding = 'latin-1'
                    with open(filename, 'r', encoding=encoding) as file:
                        for line in file:
                            line = line.split(";")
                            #skip the first line containg heading etc
                            if not first_line_skipped:
                                column = self.find_column_in_file(column, line)
                                first_line_skipped = True
                                continue
                            entity = self.do_string_preprocessing(line[column], label)
                            print(entity)
                            words = entity.split()
                            #PhraseMatcher only supports phrases up to 10 tokens
                            if len(words) < 10:
                                entity_list.append(entity.title())
        return entity_list

    def find_column_in_file(self, column, line):
        cat_counter = 0
        #find out which column contains names
        for cat in line:
            if "navn" in cat or "name" in cat:
                column = cat_counter
                break
            cat_counter += 1
        return column

    def do_string_preprocessing(self, name, label):
        #remove punctuation etc
        entity = re.sub(r'[^\w\s]','',name)
        #only remove digits from names, we want to keep them for organizations etc 
        if label == 'PER':
            entity = re.sub(r'[\d\s]','',entity)
        #remove extra whitespace after removing punctuation, otherwise it will end up as a token
        entity = re.sub(' +',' ',entity)
        return entity