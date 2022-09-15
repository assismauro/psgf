from flask_babel import lazy_gettext
class Categories:
    category = {}

    @classmethod
    def addCategory(self, name):
        Categories.category[name] = lazy_gettext(name)


Categories.addCategory('Upload')
Categories.addCategory('Pla Data')
Categories.addCategory('Queries')
Categories.addCategory('Administration')
Categories.addCategory('Inventari')
