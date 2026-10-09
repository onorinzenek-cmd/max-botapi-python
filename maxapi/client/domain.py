"""Адрес API MAX и сертификат Минцифры (октябрь 2026).

С 19.07.2026 MAX велит слать запросы на `platform-api2.max.ru` и доверять
сертификату Минцифры (документация MAX, «Changelog API»). Без этого
сертификата Python не проходит SSL нового адреса, поэтому переезд зависит
от переменной окружения `MAX_CA_BUNDLE` — пути к файлу сертификата:

- переменная задана и файл читается → новый адрес, SSL-контекст =
  стандартные сертификаты (certifi) ПЛЮС файл. Не «только файл»: ссылки
  загрузки картинок MAX выдаёт на другие адреса, их сертификаты Минцифры
  не подписывает;
- переменной нет (или пустая) → старый адрес и SSL как раньше: сервер без
  сертификата не ломается;
- путь задан, а файла нет или он не читается как сертификат → одна строка
  в лог и старый адрес.
"""

from __future__ import annotations

import os
import ssl

from typing import Optional, Tuple

from ..loggers import logger_bot


OLD_API_URL = 'https://botapi.max.ru'
NEW_API_URL = 'https://platform-api2.max.ru'
CA_BUNDLE_ENV = 'MAX_CA_BUNDLE'


def ssl_context_with_bundle(path: str) -> ssl.SSLContext:
    """Стандартные сертификаты certifi + файл Минцифры (PEM или DER)."""

    # certifi нужен только с сертификатом: без MAX_CA_BUNDLE форк
    # работает и там, где пакета нет
    import certifi

    context = ssl.create_default_context(cafile=certifi.where())

    with open(path, 'rb') as f:
        data = f.read()

    if b'BEGIN CERTIFICATE' in data:
        context.load_verify_locations(cafile=path)
    else:
        context.load_verify_locations(cadata=data)

    return context


def choose_api(ca_bundle: Optional[str]) -> Tuple[str, Optional[ssl.SSLContext]]:
    """Адрес API и SSL-контекст по пути из `MAX_CA_BUNDLE`.

    :return: (адрес, контекст); контекст None — SSL как у aiohttp по умолчанию
    """

    path = (ca_bundle or '').strip()

    if not path:
        return OLD_API_URL, None

    if not os.path.isfile(path):
        logger_bot.warning(
            f'{CA_BUNDLE_ENV}={path}: файла нет — работаю по старому адресу {OLD_API_URL}'
        )
        return OLD_API_URL, None

    try:
        context = ssl_context_with_bundle(path)
    except (OSError, ssl.SSLError, ValueError) as e:
        logger_bot.warning(
            f'{CA_BUNDLE_ENV}={path}: не читается как сертификат ({e}) — '
            f'работаю по старому адресу {OLD_API_URL}'
        )
        return OLD_API_URL, None

    logger_bot.info(f'Адрес MAX: {NEW_API_URL}, сертификат Минцифры: {path}')
    return NEW_API_URL, context
