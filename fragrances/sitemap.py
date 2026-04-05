from django.contrib.sitemaps import Sitemap

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return ['home']

    def location(self, item):
        return '/'
