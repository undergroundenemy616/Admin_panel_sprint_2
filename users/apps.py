from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

    @staticmethod
    def check_redis_connection():
        from django.core.cache import cache
        cache.set("test", "test", 10)
        cache.delete("test")

    def ready(self):
        print('Check redis engine...')
        self.check_redis_connection()
