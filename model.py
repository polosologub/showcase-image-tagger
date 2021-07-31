import pandas as pd
import numpy as np
from PIL import Image
import os
import cv2
import clip
import torch
import requests
from io import BytesIO
from collections import Counter
import yake
import spacy


###IMAGE TAGGER

#Load model
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

#Load text features (precomputed)
text_features = torch.load('data/tags2021_filtered_clip-features.pt')
text_features /= text_features.norm(dim=-1, keepdim=True)

#Set up vocabulary
tags2021 = pd.read_excel("data/tags2021_filtered.xlsx")
tags2021 = tags2021['Tag'].tolist()


def predict_image_tags(image_features, text_features=text_features, dictionary=tags2021):
    
    results = []

    for i in image_features:
        response = requests.get(i)
        img = Image.open(BytesIO(response.content))
        image_input = preprocess(img).unsqueeze(0).to(device)
        
        # Calculate features
        with torch.no_grad():
            image_features = model.encode_image(image_input)
        
        image_features /= image_features.norm(dim=-1, keepdim=True)

        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        values, indices = similarity[0].topk(5)
        
        for value, index in zip(values, indices):
            results.append((dictionary[index], round(value.item(), 4)))
    
    return results


def choose_image_tags(image_tags, max_tags):
    #get duplicates
    tags_count = Counter([x for (x,y) in image_tags]).most_common()
    duplicates = [i for (i,j) in tags_count if j > 1]
    singles = [i for (i,j) in tags_count if j == 1]
    
    if len(duplicates) == max_tags:
        return duplicates
    
    if len(duplicates) > max_tags:
        return duplicates[:max_tags]
    
    if len(duplicates) < max_tags:
        #determine how many more tags are allowed
        rest_n = max_tags - len(duplicates)

        #sort highest percentages of rest 
        rest_percentages = [tup for tup in image_tags if any(i in tup for i in singles)]
        rest_percentages.sort(key=lambda a: a[1], reverse=True)

        #choose rest_n tags
        rest_tags = [i for (i,j) in rest_percentages[:rest_n]]

        #add duplicates and rest tags 
        chosen_tags = duplicates + rest_tags

        return chosen_tags


def get_image_tags(image_links, max_tags):
    #predict tags
    image_tags = predict_image_tags(image_links)
    
    #if 1 image
    if len(image_tags) == 5:
        tags_list = [i for (i,j) in image_tags]
        return tags_list
    
    #if more than 1 image
    if len(image_tags) > 5:
        tags_list = choose_image_tags(image_tags, max_tags)
        return tags_list



####TEXT TAGGER

#load list of unwanted tags to filter keywords with
tags_filter = pd.read_excel("data/tags_filter_2021.xlsx")
tags_filter = tags_filter['Tag'].to_numpy()

#load POS tagger
nlp = spacy.load('en_core_web_sm')

stopwords = ['project', 'showcase']


def get_text_tags(text):
    #define keyword extractor
    custom_kw_extractor = yake.KeywordExtractor(lan="en", n=1, dedupLim=0.5, dedupFunc='seqm', windowsSize=1, features=None)
    
    #get POS filter of acceptable words: nouns and adv
    pos_filter = [token.text for token in nlp(text) if token.pos_ == "NOUN" or token.pos_ == "ADJ"]
    
    #generate keywords
    keywords = custom_kw_extractor.extract_keywords(text)
    
    #filter keywords and get top 5 into clean list 
    keywords = [i.capitalize() for (i,j) in keywords if i in pos_filter and i not in stopwords and i not in tags_filter][:5]
    
    return keywords



####TAG COMBINER

#when new text or image tags -> can be used with existing opposite tags
def combine_tags(image_tags, text_tags, max_tags):
    image_tags_filtered = [i for i in image_tags if not i in text_tags][:max_tags-5]
    all_tags = image_tags_filtered + text_tags
    return all_tags