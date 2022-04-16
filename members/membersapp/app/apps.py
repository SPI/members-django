from django.apps import AppConfig


class AppAppConfig(AppConfig):
    name = 'membersapp.app'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from membersapp.auth import auth_user_data_received
        from .migration import handle_user_data
        auth_user_data_received.connect(handle_user_data)
