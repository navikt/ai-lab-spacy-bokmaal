# coding: utf8
from __future__ import unicode_literals

from pathlib import Path
from spacy.util import load_model_from_init_py, get_model_meta
from spacy.language import Language
from spacy.tokens import Span
from spacy.matcher import PhraseMatcher
import os.path
from collections import defaultdict
import string
import re
import glob
import pandas as pd
import csv
import re
import sys

def read_in_files(labels: list, directory: str):
    list_of_dicts = []
    all_entities_dict = defaultdict(list)
    #find all files in chosen directory
    for file in os.listdir(directory):
        encoding = 'utf-8'
        print(file)
        if file.endswith(".csv"):
            path = os.path.join(directory, file)
            filename = re.sub('.csv', '', file)
            print(filename)
            if filename == 'land_loc':
                encoding = 'latin-1'
            label = find_label(filename, labels)
            print(label)
            if label != None:
                #get entity_list for that file and that label
                entity_list = (create_label_tuple(path, encoding, label, filename))
                for entity in entity_list:
                    all_entities_dict['label'].append(label)
                    all_entities_dict['name'].append(entity)
    print(all_entities_dict)
    new_df = pd.DataFrame.from_dict(all_entities_dict)
    new_df.to_csv(directory + 'new.csv', sep=';')

def find_label(filename: str, labels: list):
    for label in labels:
        if label.lower() in filename:
            return label
    return None
    

def load_dataframe(uri_to_file: str, encoding: str):
        path = Path(uri_to_file)
        #print(path)
        try:
            return pd.read_csv(path.absolute(), sep=";", encoding=encoding, quoting=csv.QUOTE_NONE)
        except pd.errors.EmptyDataError as err:
            print(err)


def get_processed_entities_from_column(df: pd.DataFrame, column: str, label: str) -> tuple:
    label_tuple = tuple(df[column])
    cleaned_strings = []
    for string in label_tuple:
        #pandas changes "" to nan, which is a float
        #it will throw an error
        if not isinstance(string, float):
            pre_processed_string = do_string_preprocessing(string, label)
            cleaned_strings.append(pre_processed_string)
    return cleaned_strings

def create_label_tuple(filename: str, encoding: str, label: str, file_label: str):
        label_columns =['navn','name','shortname','tettsted','kommune']
        df = load_dataframe(filename, encoding)
        result = []
        if df is not None:
            matching_columns = []
            for column in df.columns.values:
                column_clean = column.lower().strip("\"")
                if column_clean in label_columns:
                    matching_columns.append(column)
            for column in matching_columns:
                entities = get_processed_entities_from_column(df, column, label)
                for entity in entities:
                    result = add_new_entities_to_list(entity, file_label, result)
        return result

def add_new_entities_to_list(entity: str, file_label: str, entity_list: list):
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
                #Don't change case in countires names, otherwise USA will become Usa
                if file_label == 'land_loc':
                    entity_list.append(entity)
                else:
                    entity_list.append(entity.title())
        return entity_list

def find_column_in_file(columns: list, line: str):
        cat_counter = 0
        #find out which column contains names
        for cat in line:
            cat = cat.lower().strip("\"")
            if cat == 'navn' or cat == 'name' or cat == 'shortname' or cat == 'tettsted' or cat == 'kommune':
                columns.append(cat_counter)
            cat_counter += 1
        return columns

def do_string_preprocessing(name: str, label: str):
    #only remove digits from names and locations, we want to keep them for organizations etc 
    #keep - / and . in locations and names (U.S.A., Bosnia-Hercegovina, Trinid/Tobago)
    if label != 'ORG' or label != 'MISC':
        entity = re.sub(r'[^\w\s/.-]','',name)
        entity = re.sub(r'[\d]','',entity)
        #only remove whitespace at the beginning
        entity = re.sub(r'^[\s]','',entity)
        entity = re.sub(r'$[\s]','',entity)
    else:
        #remove punctuation etc
        entity = re.sub(r'[^\w\s]','',name)
    if label == 'LOC':
        entity = re.sub(r'i alt','',entity)
    #remove extra whitespace after removing punctuation, otherwise it will end up as a token
    entity = re.sub(' +',' ',entity)
    return entity

directory = 'csv_files/'
labels = ['LOC', 'PER', 'ORG', 'MISC']
read_in_files(labels, directory)