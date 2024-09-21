class ContentOption (object):
    _content_option_map = {}

    @classmethod
    def _check_option_value_types(cls, raw_option: str, value):
        types = cls._option_value_types[raw_option]

        if not type(value) in types:
            raise ValueError(
                "Option '{}' requires types {} - got type {}".format(raw_option, types, type(value))
            )
        return True

    @classmethod
    def _process_option_value(cls, raw_option: str, value):
        content_opt = cls._content_option_map[raw_option]
        content_opt._check_option_value_types(raw_option, value)
        format_func = content_opt._option_value_format.get(raw_option, None)

        if format_func:
            value = format_func(value)

        return value


    @classmethod
    def get_from_str(cls, _str):
        return cls._content_option_map[_str]


class FileOption (ContentOption):
    _process_value_map = {
        lambda value: value.__str__().lower()
    }

    _option_value_types = {
    }

    _option_value_format = {
    }


    @classmethod
    def _get_options(cls):
        return [
        ]

class FolderOption (ContentOption):
    IS_PUBLIC = "public"
    """Expected value is a bool"""
    PASSWORD = "password"
    """Expected value is a str"""
    DESCRIPTION = "description"
    """Expected value is a str"""
    TAGS = "tags"
    """Expected value is list[str]"""
    EXPIRE = "expiry"
    """Expected value is unix timestamp float or int"""

    #map that holds any extra processing to option value
    _option_value_format = {
        IS_PUBLIC: lambda value: value.__str__().lower(), #setting IS_PUBLIC requires a lowercase bool string
        TAGS: lambda value: ",".join(value) if type(value) == list else value,
        EXPIRE: lambda value: int(value) if type(value) == float else value
    }
    _option_value_types = {
        IS_PUBLIC: [bool],
        PASSWORD: [str],
        DESCRIPTION: [str],
        TAGS: [list],
        EXPIRE: [int, float]
    }

    @classmethod
    def _get_options(cls):
        return [
            cls.IS_PUBLIC,
            cls.PASSWORD,
            cls.DESCRIPTION,
            cls.TAGS,
            cls.EXPIRE
        ]

options_map = {}
for opt in FileOption._get_options():
    options_map[opt] = FileOption

for opt in FolderOption._get_options():
    options_map[opt] = FolderOption

ContentOption._content_option_map = options_map

