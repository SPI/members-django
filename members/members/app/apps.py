from django.apps import AppConfig


class AppAppConfig(AppConfig):
    name = 'members.app'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
#        from .migration import handle_user_data
        from members.auth import auth_user_data_received

        auth_user_data_received.connect(handle_user_data)
