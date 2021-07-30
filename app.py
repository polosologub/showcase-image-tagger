from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from bs4 import BeautifulSoup
import unicodedata
import model


app = Flask(__name__)
api = Api(app)

# argument parsing
img_parser = reqparse.RequestParser()
img_parser.add_argument('images', type=str, action='append')
img_parser.add_argument('max_tags', type=int, default=20)

text_parser = reqparse.RequestParser()
text_parser.add_argument('description', type=str)

combo_parser = reqparse.RequestParser()
combo_parser.add_argument('image_tags', type=str, action='append')
combo_parser.add_argument('text_tags', type=str, action='append')
combo_parser.add_argument('max_tags', type=int, default=20)


class ImageTags(Resource):
    def post(self):
        args = img_parser.parse_args()
        images = args['images']
        max_tags = args['max_tags']
        tags = model.get_image_tags(images, max_tags)
        return {'image_tags': tags}


class TextTags(Resource):
    def post(self):
        args = text_parser.parse_args()
        text = args['description']
        #remove HTML tags etc
        text = unicodedata.normalize("NFKD", BeautifulSoup(text).get_text())
        tags = model.get_text_tags(text)
        return {'text_tags': tags}


class CombinedTags(Resource):
    def post(self):
        args = combo_parser.parse_args()
        image_tags = args['image_tags']
        text_tags = args['text_tags']
        max_tags = args['max_tags']
        tags = model.combine_tags(image_tags, text_tags, max_tags)
        return {'combined_tags': tags}


api.add_resource(ImageTags, '/image-tags')
api.add_resource(CombinedTags, '/combined-tags')
api.add_resource(TextTags, '/text-tags')

        
if __name__ == "__main__":
    app.run()