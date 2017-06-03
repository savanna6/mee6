from mee6.utils import get
from random import randint

def randomize(field_name, value, light=False):
    terms = ('icon',) if light else ('icon', 'url')

    if any((term in field_name for term in terms)):
        return value + '?rand={}'.format(randint(0, 999999))
    else:
        return value

class MessageEmbed:

    top_level_fields = ['title', 'description', 'url', 'color']
    footer_fields = ['text', 'icon_url', 'proxy_icon_url']
    image_fields = ['url', 'proxy_url', 'height', 'width']
    thumbnail_fields = ['url', 'proxy_url', 'height', 'width']
    author_fields = ['name', 'url', 'proxy_icon_url', 'icon_url']


    def __init__(self):
        self.fields = []

    def add_field(self, name, value, inline=False):
        self.fields.append({'name': name,
                            'value': value,
                            'inline': inline})
        return self

    def get_dict(self):
        dct = dict()

        for field_name in self.top_level_fields:
            value = get(self, field_name)
            if value:
                dct[field_name] = value

        footer = dict()
        for field_name in self.footer_fields:
            value = get(self, 'footer_' + field_name)
            if value:
                footer[field_name] = randomize(field_name, value, light=True)
        if footer != {}:
            dct['footer'] = footer

        image = dict()
        for field_name in self.image_fields:
            value = get(self, 'image_' + field_name)
            if value:
                image[field_name] = randomize(field_name, value, light=False)
        if image != {}:
            dct['image'] = image

        thumbnail = dict()
        for field_name in self.thumbnail_fields:
            value = get(self, 'thumbnail_' + field_name)
            if value:
                thumbnail[field_name] = randomize(field_name, value,
                                                  light=False)
        if thumbnail != {}:
            dct['thumbnail'] = thumbnail

        author = dict()
        for field_name in self.author_fields:
            value = get(self, 'author_' + field_name)
            if value:
                author[field_name] = randomize(field_name, value, light=True)
        if author != {}:
            dct['author'] = author

        dct['fields'] = self.fields

        return dct

