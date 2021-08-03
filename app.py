from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from werkzeug.exceptions import HTTPException
from bs4 import BeautifulSoup
import unicodedata
import model


#Set up app
app = Flask(__name__)
api = Api(app)


# Argument parsing
tag_parser = reqparse.RequestParser()
tag_parser.add_argument('images', type=str, action='append', default=None)
tag_parser.add_argument('description', type=str, default=None)
tag_parser.add_argument('max_tags', type=int, default=20)


#Error handling
class MissingData(HTTPException):
    code = 422
    description = "At least one data input required (description and/or images)."

app.register_error_handler(MissingData, 422)


#Create endpoint
class AutoTagger(Resource):
    def post(self):
        #Get parameters
        args = tag_parser.parse_args()
        max_tags = args['max_tags']
        images = args['images']
        text = args['description']
        
        #Option 1: Only image tags
        if text is None:
            if images is not None:
                image_tags = model.get_image_tags(images, max_tags)
                return {'tags': image_tags}
            #Raise error if neither images or text were sent 
            else: 
                raise MissingData()
        
        #Option 2: Only text tags 
        if images is None:
            if text is not None:
                #remove HTML tags etc
                text = unicodedata.normalize("NFKD", BeautifulSoup(text).get_text())
                text_tags = model.get_text_tags(text)
                return {'tags': text_tags}
            #Raise error if neither images or text were sent 
            else: 
                raise MissingData()

        #Option 3: Combined tags
        else:
            #Get image tags
            image_tags = model.get_image_tags(images, max_tags)
            #Get text tags
            text = unicodedata.normalize("NFKD", BeautifulSoup(text).get_text())
            text_tags = model.get_text_tags(text)
            #Gombine tags
            combined_tags = model.combine_tags(image_tags, text_tags, max_tags)
            return {'tags': combined_tags}

api.add_resource(AutoTagger, '/autotagger')


#Run app
if __name__ == "__main__":
    app.run(debug=True)