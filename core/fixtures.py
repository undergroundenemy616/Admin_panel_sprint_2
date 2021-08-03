import copy
import functools
import logging

import orjson
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from booking_api_django_new.settings import BASE_DIR


class AddFixtures:
    def __init__(self, language):

        self.language = language
        self.logger = logging.getLogger('__name__')
        self.created = []
        self.error_count = 0
        self.warning_count = 0

    def __exclude_parent(self, item, exclude, exclude_value, default):
        for i in range(len(exclude)):
            if self.__rgetattr(item, exclude[i]) == exclude_value[i]:
                if default[i]:
                    return default[i](item)
                return True
        return False

    def add_fixture(self, model, parents=None, along_with=None, bind_with=None, *args, **kwargs):
        app_name = str(model._meta).split('.')[0].lower()
        fixtures_name = str(model._meta).split('.')[1].lower()

        data_json = self.__parse_fixtures_json(fixtures_name, app_name, *args, **kwargs)

        if not data_json:
            self.warning_count += 1
            self.logger.warning(msg=f"Fixtures {fixtures_name} for {app_name} doesn't support selected language ")
            self.logger.warning(msg=f"Skip to next...")
            return f"Fixtures {fixtures_name} for {app_name} doesn't support selected language "
        elif type(data_json) == str:
            return data_json

        if parents:
            result = []
            for item in parents['values']:
                if parents.get('exclude'):
                    if self.__exclude_parent(item, parents['exclude'], parents['exclude_value'], parents['default']):
                        continue

                temp = self.__fixture_logging_decorator(self.__fixtures_create, fixtures_name, **{
                    "model": model, "data_json": data_json, "parent": {parents['parameter']: item},
                    "along_with": along_with, "bind_with": bind_with})
                if not temp:
                    return temp
                result.extend(temp)
                if parents.get('not_strict') and len(data_json) <= len(result):
                    break
            self.created.append(f"Created {fixtures_name}: {len(result)}")
            return result

        result = self.__fixture_logging_decorator(self.__fixtures_create, fixtures_name, **{
            "model": model, "data_json": data_json, "along_with": along_with, "bind_with": bind_with})

        self.created.append(f"Created {fixtures_name}: {len(result)}")
        return result

    def __parse_fixtures_json(self, fixtures_name, app_name=None, *args, **kwargs):
        if not app_name:
            app_name = fixtures_name
        try:
            with open(BASE_DIR + f'/{app_name}/fixtures/{fixtures_name}_{self.language}.json') as file:
                result = orjson.loads(file.read())
        except FileNotFoundError:
            return None
        return result

    def __fixtures_create(self, model, data_json, along_with=None, bind_with=None, parent=None, **kwargs):
        result = []
        for item in data_json:
            entity = copy.deepcopy(item.get(str(model._meta).split('.')[1].lower()))

            if not entity:
                return f"Wrong format of json file for {str(model._meta).split('.')[1].lower()}"
            if parent:
                entity.update(parent)

            if bind_with:
                add = []
                for params in bind_with:
                    many_to_many_list = []
                    for temp in entity[params['parameter']]:
                        value = self.__get_filter(params['on_value'], params['values'], temp)
                        if value:
                            many_to_many_list.append(value.id)
                        else:
                            self.warning_count += 1
                            self.logger.warning(msg=f"Can't find {temp} in transferred data")

                    temp = [params['parameter'], many_to_many_list]
                    add.append(temp)
                    del entity[params['parameter']]

            if along_with:
                for params in along_with:
                    temp = self.__get_filter(params['on_value'], params['values'], entity[params['parameter']])
                    if not temp:
                        self.warning_count += 1
                        self.logger.warning(msg=f"Can't find {entity[params['parameter']]} in transferred data")
                    entity[params['parameter']] = temp

            try:
                created = model.objects.create(**entity)
            except IntegrityError:
                self.warning_count += 1
                self.logger.warning(msg=f"This {str(model._meta).split('.')[1].lower()} already exist: {entity}")
                self.logger.warning(msg="Skip to next...")
                continue
            if bind_with:
                for temp in add:
                    try:
                        getattr(created, temp[0]).add(*temp[1])
                    except ValidationError as error:
                        return error.messages
            result.append(created)
        return result

    @staticmethod
    def __get_filter(parameter, list_query, value):
        for item in list_query:
            if getattr(item, parameter) == value:
                return item
        return None

    def __fixture_logging_decorator(self, func, name, *args, **kwargs):
        self.logger.warning(f"Start adding {name}.")
        result = func(*args, **kwargs)
        if type(result) == str:
            self.created.append(f"Entity {name} wasn't created")
            self.logger.error(msg=f"Error with adding {name}:")
            self.error_count += 1
            self.logger.error(msg=result)
            self.logger.error(msg="Proceed")
            self.logger.error('--------------')
            return None
        self.logger.warning(f"Adding for {name} finished.")
        self.logger.warning('--------------')
        return result

    def print_result(self):
        self.logger.warning(msg=f"Adding fixtures complete. Number of errors: {self.error_count}")
        self.logger.warning(msg=f"                          Number of warnings: {self.warning_count}")
        for message in self.created:
            self.logger.warning(msg=message)

    @staticmethod
    def __rgetattr(obj, path):
        return functools.reduce(getattr, path.split('.'), obj)
