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
import pandas as pd
import csv


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
            for label, text in self.entities.items():
                for token in text:
                    patterns[label].append(nlp(token))

        for label, pattern in patterns.items():
            print(label)
            print(pattern)
            self.matcher.add(label, None,  *pattern)
    
    def __call__(self, doc):
        matches = self.matcher(doc)
        spans = []  # keep the spans for later so we can merge them afterwards
        for label_id, start, end in matches:
            # create Span for matched entity and assign label
            entity = Span(doc, start, end, label=label_id)
            entity._.via_patterns = True
            print("entity: ")
            #that's a string
            print(entity.text)
            spans.append(entity)
            print("tokens in that entity: ")
            token_lemma = ""
            for token in doc[start:end]:
                print(token)
                if token_lemma == "":
                    token_lemma = token.lemma_
                else:
                    token_lemma = token_lemma + " " + token.lemma_

            for token in doc[start:end]:
                token.tag_ = 'PROPN___'
                token.lemma_ = token_lemma.lower()
            print("")
            
        doc.ents = list(doc.ents) + spans  # overwrite doc.ents and add entities – don't replace!
        for span in spans:
            span.merge()  # merge all spans at the end to avoid mismatched indices
        return doc  # don't forget to return the Doc!

    def load_dataframe(self, uri_to_file:str, encoding:str):
        path = Path(uri_to_file)
        print(path)
        try:
            return pd.read_csv(path.absolute(), sep=";", encoding=encoding, quoting=csv.QUOTE_NONE)
        except pd.errors.EmptyDataError as err:
            print(err)


    def extract_column(self, df: pd.DataFrame, column: str, label:str) -> tuple:
        lable_tuple = tuple(df[column])
        cleaned_strings = []
        for string in lable_tuple:
            pre_processed_string = self.do_string_preprocessing(string, label)
            cleaned_strings.append(pre_processed_string)
        return cleaned_strings
    
    def get_entities(self, label):
        entity_dict = {}
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
                    if file_label == 'land_loc':
                        encoding = 'latin-1'

                    if label in entity_dict.keys():
                        entity_dict[label] = entity_dict[label] + self.create_label_tuple(filename, encoding, label, file_label)
                    else:
                        entity_dict = {label: self.create_label_tuple(filename, encoding, label, file_label)}

        return entity_dict
              
    def create_label_tuple(self, filename:str, encoding:str, label:str, file_label:str) -> dict:
        label_columns =['navn','name','shortname','tettsted','kommune']
        df = self.load_dataframe(filename, encoding)
        result = []
        if df is not None:
            matching_columns = []
            for column in df.columns.values:
                column_clean = column.lower().strip("\"")
                if column_clean in label_columns:
                    matching_columns.append(column)
            for column in matching_columns:
                entities = self.extract_column(df, column, label)
                for entity in entities:
                    result = self.add_new_entities_to_list(entity, file_label, result)
        return result

    def add_new_entities_to_list(self, entity, file_label, entity_list):
        words = entity.split()
        #PhraseMatcher only supports phrases up to 10 tokens
        #don't add duplicates
        #don't allow empty tokens, it throws ValueError: [T001] Max length currently 10 for phrase matching
        if len(words) < 10 and entity.title() not in entity_list and entity != "":# and entity not in nlp.vocab:
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
        #find out which column contains names
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