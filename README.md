# Showcase Image Tagger
 
 Get automated tags for UAL Graduate Showcase projects containing images and text descriptions. 

## Technical Documentation

This is a REST API that can be used for suggesting tags to students when they upload projects to the UAL Portfolio website.
 
The tool consists of three parts:

 1. An image tagger predicting official UAL showcase tags using CLIP.

 2. A text tagger generating tags based on project descriptions using the YAKE keyword extractor. 

 3. A function combining both sets of tags into one list with a maximum length. 


## Usage

### Get tags 
Get a list of tags.

#### Endpoint

`POST /autotagger`

#### Body Parameters

|Parameter|Type|Description|Default|   
|---------|----|-----------|-------|     
`images`|`array, items: string`| **Optional.** An array of image URLs. Only accepts JPG, JPEG, PNG and GIF file extensions.|`Null`  
`description`| `string`| **Optional.** The project description text.|`Null`
|`max_tags`|`integer`|**Optional.** The maximum length of the tags list. Applies to image tags and combined image and text tags. Text tags on their own always contain 5 tags.|`20`



**Important:** While both `images` and `description` are optional, at least one of them has to be included. 

#### Status Codes

|Code|Description|
|----|-----------|
|`200`|Success|
|`422`|At least one data input required (description and/or images).|


#### Example Request Body
```
{
    "images": [
        "https://s3-eu-west-2.amazonaws.com/portfolio-tools/wp-content/uploads/2020/07/16151416/Screenshot-2020-07-16-at-16.04.08-1.png",
        "https://s3-eu-west-2.amazonaws.com/portfolio-tools/wp-content/uploads/2020/07/16150447/Screenshot-2020-07-16-at-16.03.41.png",
        "https://s3-eu-west-2.amazonaws.com/portfolio-tools/wp-content/uploads/2020/07/16150733/Screenshot-2020-07-16-at-16.03.49.png",
        "https://s3-eu-west-2.amazonaws.com/portfolio-tools/wp-content/uploads/2020/07/16150739/Screenshot-2020-07-16-at-16.03.58.png",
        "https://s3-eu-west-2.amazonaws.com/portfolio-tools/wp-content/uploads/2020/07/16150740/Screenshot-2020-07-16-at-16.04.08.png",
        "https://s3-eu-west-2.amazonaws.com/portfolio-tools/wp-content/uploads/2020/07/16150820/Screenshot-2020-07-16-at-16.04.16-1.png"
        ],
    "description": "<p> Garments in the collection have been designed to reveal areas of sexual significance to liberate women from moralised sexuality that stems from patriarchal ideals. </p>"
}
```

#### Example JSON Response

```
{
    "tags": [
        "Triptych",
        "Light",
        "SpeculativeDesign",
        "Lights",
        "ProjectionMapping",
        "SustainableFashion",
        "35mm",
        "FashionFutures",
        "Biophilia",
        "Floral",
        "Interior",
        "FashionPhotography",
        "Florals",
        "HairSculpture",
        "Knitwear",
        "FashionCampaign",
        "Headpieces",
        "StillLife",
        "Plants",
        "FashionMagazine"
    ]
}
```






## To do:
- [ ] Add security 
- [ ] Deploy API on CCI server
- [ ] Write documentation

