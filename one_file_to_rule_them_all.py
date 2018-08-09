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
    all_entities_dict = defaultdict(list)
    #find all files in chosen directory
    for file in os.listdir(directory):
        encoding = 'utf-8'
        if file.endswith(".csv"):
            path = os.path.join(directory, file)
            filename = re.sub('.csv', '', file)
            if filename == 'land_loc':
                encoding = 'latin-1'
            label = find_label(filename, labels)
            if label != None:
                #get entity_list for that file and that label
                entity_list = get_entity_list(path, encoding, label, filename)
                for entity in entity_list:
                    all_entities_dict['label'].append(label)
                    all_entities_dict['name'].append(entity)
    #create DataFrame from pairs of label and name
    new_df = pd.DataFrame.from_dict(all_entities_dict)
    new_df.to_csv(directory + 'new.csv', sep=';')

def find_label(filename: str, labels: list):
    #the names of the files have to contain one of the specified labels so that we know which label to tag the entities in that file with
    for label in labels:
        if label.lower() in filename:
            return label
    return None
    
def get_entity_list(filename: str, encoding: str, label: str, file_label: str):
    df = load_dataframe(filename, encoding)
    result = []
    if df is not None:
        relevant_columns = find_relevant_columns(df)
        for column in relevant_columns:
            entities = get_processed_entities_from_column(df, column, label)
            updated_entities = filter_out_and_split_entities(entities, file_label)
            for entity in updated_entities:
                #don't add duplicates
                if entity not in result:
                    result.append(entity)
    return result

def load_dataframe(uri_to_file: str, encoding: str):
        path = Path(uri_to_file)
        try:
            return pd.read_csv(path.absolute(), sep=";", encoding=encoding, quoting=csv.QUOTE_NONE)
        except pd.errors.EmptyDataError as err:
            print(err)

def find_relevant_columns(df: pd.DataFrame):
    #only keep column names that are relevant, clean them up
    label_columns =['navn','name','shortname','tettsted','kommune']
    relevant_columns = []
    for column in df.columns.values:
        column_clean = column.lower().strip("\"")
        if column_clean in label_columns:
            relevant_columns.append(column)
    return relevant_columns

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

def do_string_preprocessing(name: str, label: str):
    #only remove digits from names and locations, we want to keep them for organizations etc 
    #keep - / and . in locations and names (U.S.A., Bosnia-Hercegovina, Trinid/Tobago)
    if label != 'ORG' or label != 'MISC':
        entity = re.sub(r'[^\w\s/.-]','',name)
        entity = re.sub(r'[\d]','',entity)
        #only remove whitespace at the beginning and end
        entity = re.sub(r'^[\s]','',entity)
        entity = re.sub(r'$[\s]','',entity)
    else:
        #remove punctuation etc
        entity = re.sub(r'[^\w\s]','',name)
    if label == 'LOC':
        #remove 'i alt' from some cities' names
        entity = re.sub(r'i alt','',entity)
    #remove extra whitespace after removing punctuation, otherwise it will end up as a separate token
    entity = re.sub(' +',' ',entity)
    return entity

def filter_out_and_split_entities(entities_list: list, file_label: str):
    new_entities = []
    #PhraseMatcher only supports phrases up to 10 tokens
    #don't add duplicates
    #don't allow empty tokens, it throws ValueError: [T001] Max length currently 10 for phrase matching
    for entity in entities_list:
        words = entity.split()
        if len(words) < 10 and entity.title() and entity != "":# and entity not in nlp.vocab:
            #the cities' names with / in this file have to be split in 2 separate entities
            if file_label == 'tettsteder_loc' and '/' in entity:
                entities = entity.split('/')
                for e in entities:
                    new_entities.append(e.title())
            else:
                #Don't change case in countries' names, otherwise USA will become Usa
                if file_label == 'land_loc':
                    new_entities.append(entity)
                else:
                    new_entities.append(entity.title())
    return new_entities

directory = 'csv_files/'
labels = ['LOC', 'PER', 'ORG', 'MISC']
read_in_files(labels, directory)