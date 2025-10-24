from django.apps import AppConfig


class BusAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bus_app'

    def ready(self):
        import bus_app.signals