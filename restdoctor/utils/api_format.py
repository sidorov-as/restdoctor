from __future__ import annotations

import functools
import typing

from restdoctor.constants import DEFAULT_PREFIX_FORMAT_VERSION


def _find_format_range(name_format: str) -> typing.List[int]:
    is_block = False
    current_number = []
    versions_pool = []
    for word in name_format:
        if word == '{':
            is_block = True
        if is_block and word.isdigit():
            current_number.append(word)
        if is_block and word == ',':
            versions_pool.append(int(''.join(current_number)))
            current_number = []
        if word == '}':
            if current_number:
                versions_pool.append(int(''.join(current_number)))
            break
    versions_pool = sorted(versions_pool)
    return versions_pool


@functools.lru_cache
def generate_format(
    api_format: str, api_format_version: typing.Optional[int] = None
) -> typing.List[str]:
    if DEFAULT_PREFIX_FORMAT_VERSION not in api_format:
        return [api_format]

    api_format_name, api_format_prefix = api_format.split(DEFAULT_PREFIX_FORMAT_VERSION, 1)
    format_range = _find_format_range(api_format_prefix)
    if not format_range:
        return [api_format]
    result = []
    for version in format_range:
        if not api_format_version or version <= api_format_version:
            result.append(f'{api_format_name}{DEFAULT_PREFIX_FORMAT_VERSION}{version}')
    return result


def get_available_format(available_formats: typing.Tuple[str, ...]) -> typing.List[str]:
    result = []
    for api_format in available_formats:
        result.extend(generate_format(api_format))
    return result


def get_filter_formats(
    available_formats: typing.Tuple[str, ...], requested_format: str
) -> typing.List[str]:
    result = generate_format(requested_format)
    try:
        search_prefix, api_format_prefix = requested_format.split(DEFAULT_PREFIX_FORMAT_VERSION, 1)
        api_format_version = int(api_format_prefix)
    except ValueError:
        return result

    for api_format in available_formats:
        if api_format.startswith(search_prefix) and api_format != requested_format:
            result = generate_format(api_format, api_format_version)
    return result
