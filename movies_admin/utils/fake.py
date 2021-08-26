from faker import Faker as BaseFaker


class Faker(object):
    def __init__(self, seed=123, locale='ru_RU'):
        self._faker = BaseFaker(locale=locale)
        self._faker.seed_instance(seed)

    def __getattr__(self, item):
        return getattr(self._faker, item)


my_faker = Faker()
