from django.apps import AppConfig


class FragrancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fragrances'
    
    def ready(self):
        import fragrances.signals
