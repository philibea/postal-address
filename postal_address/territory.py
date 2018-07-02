# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2017 Scaleway and Contributors. All Rights Reserved.
#                         Kevin Deldycke <kdeldycke@scaleway.com>
#
# Licensed under the BSD 2-Clause License (the "License"); you may not use this
# file except in compliance with the License. You may obtain a copy of the
# License at http://opensource.org/licenses/BSD-2-Clause

u""" Utilities to normalize and reconcile territory codes.

.. data:: FOREIGN_TERRITORIES_MAPPING

    Reference *valid* country_codes as keys that are foreign territories of
    another country. The latter is the dictionary value.

.. data:: COUNTRY_ALIASES

    Bind *invalid* country_code in the ISO-3166 meaning with their *valid*
    iso counterpart.
    This enables us to handle so special cases of commonly used country codes
    that are not part of the ISO-3166 definitions.

.. data:: SUBDIVISION_COUNTRIES

   Map subdivision ISO 3166-2 codes to their officially assigned ISO 3166-1
   alpha-2 country codes. Source: https://en.wikipedia.org/wiki
   /ISO_3166-2#Subdivisions_included_in_ISO_3166-1

.. data:: SUBDIVISION_ALIASES

    Map some subdivision aliases representing the same territory, but defined
    under different countries.

.. data:: FOREIGN_TERRITORIES_ALIAS_TO_COUNTRY

    Bind *invalid* country_code in the ISO-3166 (mostly subdivisions)
    representing territories to *valid* iso country codes representing
    the main country of this territory.

.. data:: COUNTRY_ALIAS_TO_SUBDIVISION

    Bind *invalid* country_code to their real subdivision code.

.. data:: REVERSE_MAPPING

   Reverse index of the SUBDIVISION_COUNTRIES mapping defined above.
"""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

from itertools import chain
from operator import attrgetter

from boltons.cacheutils import cached, LRI
from pycountry import countries, subdivisions

from . import PY2

if PY2:
    from itertools import imap, ifilter
else:
    imap = map
    ifilter = filter


FOREIGN_TERRITORIES_MAPPING = {
    'CC': 'AU',  # Cocos Island,                      Australian territory
    'HM': 'AU',  # Heard Island and McDonald Islands, Australian territory
    'JE': 'BR',  # Jersey,                            Brazilian territory
    'HK': 'CN',  # Hong Kong,                         Chinese territory
    'MO': 'CN',  # Macao,                             Chinese territory
    'FO': 'DK',  # Faroe Islands,                     Danish territory
    'AX': 'FI',  # Åland,                             Finnish territory
    'AQ': 'FR',  # Antarctica,                        French territory
    'BL': 'FR',  # Saint Barthelemy,                  French territory
    'GF': 'FR',  # French Guiana,                     French territory
    'GP': 'FR',  # Guadeloupe,                        French territory
    'GY': 'FR',  # Guyana,                            French territory
    'MF': 'FR',  # Saint Martin,                      French territory
    'MQ': 'FR',  # Martinique,                        French territory
    'NC': 'FR',  # New Caledonia,                     French territory
    'PF': 'FR',  # French Polynesia,                  French territory
    'PM': 'FR',  # Saint Pierre and Miquelon,         French territory
    'RE': 'FR',  # Reunion,                           French territory
    'TF': 'FR',  # French Southern Territories,       French territory
    'WF': 'FR',  # Wallis and Futuna,                 French territory
    'YT': 'FR',  # Mayotte,                           French territory
    'GI': 'GB',  # Gibraltar,                         British territory
    'IM': 'GB',  # Isle of Man,                       British territory
    'IO': 'GB',  # British Indian Ocean Territory,    British territory
    'PN': 'GB',  # Pitcairn,                          British territory
    'SH': 'GB',  # Saint Helena,                      British territory
    'VG': 'GB',  # British Virgin Islands,            British territory
    'BQ': 'NL',  # Bonaire,                           Dutch territory
    'SX': 'NL',  # Sint Maarten,                      Dutch territory
    'BV': 'NO',  # Bouvet Island,                     Norwegian territory
    'SJ': 'NO',  # Svalbard and Jan Mayen,            Norwegian territory
    'AS': 'US',  # American Samoa,                    American territory
    'GU': 'US',  # Guam,                              American territory
    'MP': 'US',  # Northern Mariana Islands,          American territory
    'VI': 'US',  # US Virgin Islands,                 American territory
}

COUNTRY_ALIASES = {
    'UK': 'GB',  # United Kingdom is known as 'GB' in ISO-3166
    'EL': 'GR',  # 'EL' is the european version of Greece,
}

SUBDIVISION_COUNTRIES = {
    'CN-71': 'TW',  # Taiwan
    'CN-91': 'HK',  # Hong Kong
    'CN-92': 'MO',  # Macao
    'FI-01': 'AX',  # Åland
    'FR-BL': 'BL',  # Saint Barthélemy
    'FR-GF': 'GF',  # French Guiana
    'FR-GP': 'GP',  # Guadeloupe
    'FR-MF': 'MF',  # Saint Martin
    'FR-MQ': 'MQ',  # Martinique
    'FR-NC': 'NC',  # New Caledonia
    'FR-PF': 'PF',  # French Polynesia
    'FR-PM': 'PM',  # Saint Pierre and Miquelon
    'FR-RE': 'RE',  # Réunion
    'FR-TF': 'TF',  # French Southern Territories
    'FR-WF': 'WF',  # Wallis and Futuna
    'FR-YT': 'YT',  # Mayotte
    'NL-AW': 'AW',  # Aruba
    'NL-CW': 'CW',  # Curaçao
    'NL-SX': 'SX',  # Sint Maarten
    'NO-21': 'SJ',  # Svalbard
    'NO-22': 'SJ',  # Jan Mayen
    'US-AS': 'AS',  # American Samoa
    'US-GU': 'GU',  # Guam
    'US-MP': 'MP',  # Northern Mariana Islands
    'US-PR': 'PR',  # Puerto Rico
    'US-UM': 'UM',  # United States Minor Outlying Islands
    'US-VI': 'VI',  # Virgin Islands, U.S.
}

SUBDIVISION_ALIASES = {
    'NL-BQ1': 'BQ-BO',  # Bonaire
    'NL-BQ2': 'BQ-SA',  # Saba
    'NL-BQ3': 'BQ-SE',  # Sint Eustatius
}

FOREIGN_TERRITORIES_ALIAS_TO_COUNTRY = {
    # Source:
    # https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Exceptional_reservations
    'DG': 'IO',  # Diego Garcia is part of the British Indian Ocean Territory
    'FX': 'FR',  # France, Metropolitan
    # European Commision country code exceptions.
    # Source: http://publications.europa.eu/code/pdf/370000en.htm#pays
    'EA': 'ES',  # 'EA' is the union of Ceuta and Melilla, Spanish territory
}

COUNTRY_ALIAS_TO_SUBDIVISION = {
    'AC': 'SH-AC',  # Ascension Island
    'CP': 'FR-CP',  # Clipperton Island
    'IC': 'ES-CN',  # Canary Islands
    'TA': 'SH-TA',  # Tristan da Cunha
}


# Build the reverse index of aliases defined above.
REVERSE_MAPPING = {}
for reverse_mapping in [SUBDIVISION_COUNTRIES]:
    for alias_code, target_code in reverse_mapping.items():
        REVERSE_MAPPING.setdefault(target_code, set()).add(alias_code)

for straight_mapping in [FOREIGN_TERRITORIES_ALIAS_TO_COUNTRY,
                         COUNTRY_ALIASES,
                         SUBDIVISION_ALIASES,
                         FOREIGN_TERRITORIES_MAPPING]:
    for alias_code, target_code in straight_mapping.items():
        REVERSE_MAPPING.setdefault(alias_code, set()).add(target_code)

@cached(LRI())
def supported_territory_codes():
    """ Return a set of recognized territory codes.
    """
    return supported_country_codes().union(supported_subdivision_codes())


@cached(LRI())
def supported_country_codes():
    """ Return a set of recognized country codes.

    Are supported:
        * ISO 3166-1 alpha-2 country codes and exceptional reservations
        * European Commision country code exceptions
    """
    return set(chain(
        imap(attrgetter('alpha_2'), countries),
        # Include ISO and EC exceptions.
        COUNTRY_ALIASES.keys(), FOREIGN_TERRITORIES_ALIAS_TO_COUNTRY.keys(),
        COUNTRY_ALIAS_TO_SUBDIVISION.keys()))


@cached(LRI())
def supported_subdivision_codes():
    """ Return a set of recognized subdivision codes.

    Are supported:
        * ISO 3166-2 subdivision codes
    """
    return set(imap(attrgetter('code'), subdivisions))


def normalize_territory_code(territory_code, resolve_aliases=True,
                             resole_foreign_territory=False):
    """Normalize any string into a territory code.

    :param territory_code: The input string to normalize.
    :param resolve_aliases: Trigger alias computation.
    :param resole_foreign_territory: Trigger foreign country computation.
    :return: The resolved territory code.
    """
    territory_code = territory_code.strip().upper()
    if territory_code not in supported_territory_codes():
        raise ValueError(
            'Unrecognized {!r} territory code.'.format(territory_code))

    # We resolve country aliases and subdivision aliases
    # nevertheless since their keys does not exists in pycountry!
    territory_code = FOREIGN_TERRITORIES_ALIAS_TO_COUNTRY.get(territory_code,
                                                              territory_code)
    territory_code = COUNTRY_ALIASES.get(territory_code,
                                         territory_code)
    if resolve_aliases:
        territory_code = SUBDIVISION_ALIASES.get(
            territory_code, territory_code)
        territory_code = SUBDIVISION_COUNTRIES.get(
            territory_code, territory_code)
    if resole_foreign_territory:
        territory_code = territory_attachment(territory_code)
    return territory_code


def territory_attachment(country_code):
    """Returns the ISO-3166 alpha2 country_code of the country of which the
    given country is part of.

    :param country_code: The foreign territory to lookup.
    :return: The main country of this foreign territory,
    the input country_code if None.
    """
    return FOREIGN_TERRITORIES_MAPPING.get(country_code, country_code)


def country_from_subdivision(subdivision_code):
    """ Return the normalized country code from a subdivision code.

    If no country is found, or the subdivision code is incorrect, ``None`` is
    returned.

    For subdivisions having their own ISO 3166-1 alpha-2 country code, returns
    the later instead of the parent ISO 3166-2 top entry.
    """
    # Resolve subdivision alias.
    code = SUBDIVISION_COUNTRIES.get(subdivision_code, subdivision_code)

    # We have a country code, return it right away.
    if code in supported_country_codes():
        return code

    # Try to extract country code from subdivision.
    try:
        subdiv = subdivisions.get(code=code)
    except KeyError:
        return None
    return subdiv.country_code


def default_subdivision_code(country_code):
    """ Return the default subdivision code of a country.

    The result can be guessed only if there is a 1:1 mapping between a country
    code and a subdivision code.
    """
    # Build the reverse index of the subdivision/country alias mapping.
    default_subdiv = {}
    for subdiv_code, alias_code in SUBDIVISION_COUNTRIES.items():
        # Skip non-country
        if len(alias_code) == 2:
            default_subdiv.setdefault(alias_code, set()).add(subdiv_code)

    # Include countries directly mapping to a subdivision.
    for alias_code, subdiv_code in COUNTRY_ALIAS_TO_SUBDIVISION.items():
            default_subdiv.setdefault(alias_code, set()).add(subdiv_code)

    default_subdivisions = default_subdiv.get(country_code)

    if default_subdivisions and len(default_subdivisions) == 1:
        return default_subdivisions.pop()


def territory_children_codes(territory_code, include_self=False):
    """ Return a set of subdivision codes from all sub-levels.

    All returned codes are normalized, including self.
    """
    codes = set()

    code = normalize_territory_code(territory_code)

    # We have a country code, look for matching subdivisions in one pass.
    if code in supported_country_codes():
        codes.update(imap(
            attrgetter('code'),
            ifilter(lambda subdiv: subdiv.country_code == code, subdivisions)))

    # Engage the stupid per-level recursive brute-force search as pycountry
    # only expose the child-parent relationship upwards.
    else:
        direct_children_codes = set(imap(
            attrgetter('code'),
            ifilter(lambda subdiv: subdiv.parent_code == code, subdivisions)))
        for child_code in direct_children_codes:
            codes.update(
                territory_children_codes(child_code, include_self=True))

    if include_self:
        codes.add(code)

    return codes


def territory_parents(territory_code, include_country=True):
    """ Return the whole hierarchy of territories, up to the country.

    Values returned by the generator are either subdivisions or country
    objects, starting from the provided territory and up its way to the top
    administrative territory (i.e. country).
    """
    tree = []

    # If the provided territory code is a country, return it right away.
    territory_code = normalize_territory_code(territory_code)
    if territory_code in supported_country_codes():
        if include_country:
            tree.append(countries.get(alpha_2=territory_code))
        return tree

    # Else, resolve the territory as if it's a subdivision code.
    subdivision_code = territory_code
    while subdivision_code:
        subdiv = subdivisions.get(code=subdivision_code)
        tree.append(subdiv)
        if not subdiv.parent_code:
            break
        subdivision_code = subdiv.parent_code

    # Return country
    if include_country:
        tree.append(subdivisions.get(code=subdivision_code).country)

    return tree


def territory_parents_codes(territory_code, include_country=True):
    """ Like territory_parents but return normalized codes instead of objects.
    """
    for territory in territory_parents(
            territory_code, include_country=include_country):
        full_class_name = '{}.{}'.format(
            territory.__module__, territory.__class__.__name__)
        if full_class_name == 'pycountry.db.Country':
            yield territory.alpha_2
        elif full_class_name == 'pycountry.db.Subdivision':
            yield territory.code
        else:
            raise "Unrecognized {!r} territory.".format(territory)


def country_aliases(territory_code):
    """ List valid country code aliases of a territory.

    Mainly used to check if a non-normalized country code can safely be
    replaced by its normalized form.
    """
    country_codes = set()

    # Add a country code right away in our aliases.
    if territory_code in supported_country_codes():
        country_codes.add(territory_code)

    # A subdivision code triggers a walk along the non-normalized parent tree
    # and look for aliases at each level.
    else:
        subdiv = subdivisions.get(code=territory_code)
        parent_code = subdiv.parent_code
        if not parent_code:
            parent_code = subdiv.country.alpha_2
        country_codes.update(country_aliases(parent_code))
        # Adding subdivision's country alias
        if territory_code in SUBDIVISION_COUNTRIES:
            country_codes.update({SUBDIVISION_COUNTRIES.get(territory_code)})

    # Hunt for aliases
    for mapped_code in REVERSE_MAPPING.get(territory_code, []):
        country_codes.update(country_aliases(mapped_code))

    return country_codes
