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

#Predict top 5 tags for each image 
def predict_image_tags(images, text_features=text_features, vocabulary=tags2021):
    
    results = []

    for i in images:
        #Load and preprocess images from URLs
        response = requests.get(i)
        img = Image.open(BytesIO(response.content))
        image_input = preprocess(img).unsqueeze(0).to(device)
        
        #Calculate image features
        with torch.no_grad():
            image_features = model.encode_image(image_input)
        image_features /= image_features.norm(dim=-1, keepdim=True)

        #Get cosine similarity scores between image and text features and pick top 5 tags 
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        values, indices = similarity[0].topk(5)
        
        #Put top 5 tags with probability scores into array
        for value, index in zip(values, indices):
            results.append((vocabulary[index], round(value.item(), 4)))
    
    return results

#Get a curated list of top n tags for all images in a project
def choose_image_tags(image_tags, max_tags):
    #Choose duplicate tags across images first, the most mentioned tags go on top
    tags_count = Counter([x for (x,y) in image_tags]).most_common()
    duplicates = [i for (i,j) in tags_count if j > 1]
    singles = [i for (i,j) in tags_count if j == 1]
    
    if len(duplicates) == max_tags:
        return duplicates
    
    if len(duplicates) > max_tags:
        return duplicates[:max_tags]
    
    #If there is still room for more tags, pick more tags with the highest probabilities
    if len(duplicates) < max_tags:
        #Determine how many more tags are allowed
        rest_n = max_tags - len(duplicates)

        #Sort highest percentages of rest tags
        rest_percentages = [tup for tup in image_tags if any(i in tup for i in singles)]
        rest_percentages.sort(key=lambda a: a[1], reverse=True)

        #Choose rest_n tags
        rest_tags = [i for (i,j) in rest_percentages[:rest_n]]

        #Add duplicates tags and rest tags into one array
        chosen_tags = duplicates + rest_tags

        return chosen_tags

#Predict image tags and get the curated list in one go
def get_image_tags(images, max_tags):
    #predict tags
    image_tags = predict_image_tags(images)
    
    #if 1 image just return the tags (since there is only 5 tags per image)
    if len(image_tags) == 5:
        tags_list = [i for (i,j) in image_tags]
        return tags_list
    
    #if more than 1 image get a curated list
    if len(image_tags) > 5:
        tags_list = choose_image_tags(image_tags, max_tags)
        return tags_list



####TEXT TAGGER

#Load list of unwanted tags to filter keywords with
tags_filter = pd.read_excel("data/tags_filter_2021.xlsx")
tags_filter = tags_filter['Tag'].to_numpy()

#Define keyword extractor
custom_kw_extractor = yake.KeywordExtractor(lan="en", n=1, dedupLim=0.5, dedupFunc='seqm', windowsSize=1, features=None)

#Load POS tagger 
nlp = spacy.load('en_core_web_sm')

#Remove these tags as they are too self-explanatory 
stopwords = ['project', 'showcase']

#Get top 5 keyword tags
def get_text_tags(text):
    #Get a list of acceptable tokens from the input text through POS tagging -> we only want nouns and adjectives for useful tags
    pos_filter = [token.text for token in nlp(text) if token.pos_ == "NOUN" or token.pos_ == "ADJ"]

    #Generate keywords
    keywords = custom_kw_extractor.extract_keywords(text)
    
    #Filter keywords and get top 5 tags
    keywords = [i.capitalize() for (i,j) in keywords if i in pos_filter and i not in stopwords and i not in tags_filter][:5]
    
    return keywords



####TAG COMBINER

#This will get a combined list of top n image and text tags 
def combine_tags(image_tags, text_tags, max_tags):
    #Remove any image tags that exist in the text tags and get the top n image tags minus 5 (to make room for the 5 text tags)
    image_tags_filtered = [i for i in image_tags if not i in text_tags][:max_tags-5]
    #Combine remaining image tags and text tags into one list
    all_tags = image_tags_filtered + text_tags
    return all_tags