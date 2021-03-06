# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import division

from numpy import floor, arange, array, where
from openfisca_france.model.base import QUIMEN


PREF = QUIMEN['pref']
CREF = QUIMEN['cref']
ENFS = [QUIMEN['enf{}'.format(i)] for i in range(1, 10)]


def _nbinde(self, age_en_mois_holder):
    """
    Number of household members
    'men'
    Values range between 1 and 6 for 6 members or more
    """
    age_en_mois = self.split_by_roles(age_en_mois_holder)

    n1 = 0
    for ind in age_en_mois.iterkeys():
        n1 += 1 * (floor(age_en_mois[ind]) >= 0)
    n2 = where(n1 >= 6, 6, n1)
    return n2


def _ageq(age_en_mois):
    '''
    Calcule la tranche d'âge quinquennal
    moins de 25 ans : 0
    25 à 29 ans     : 1
    30 à 34 ans     : 2
    35 à 39 ans     : 3
    40 à 44 ans     : 4
    45 à 49 ans     : 5
    50 à 54 ans     : 6
    55 à 59 ans     : 7
    60 à 64 ans     : 8
    65 à 69 ans     : 9
    70 à 74 ans     :10
    75 à 79 ans     :11
    80 ans et plus  :12
    'ind'
    '''
    age = floor(age_en_mois / 12)
    tranche = array([(age >= ag) for ag in arange(25, 5, 81)]).sum(axis = 0)
    return tranche


def _nb_ageq0(self, age_en_mois_holder):
    '''
    Calcule le nombre d'individus dans chaque tranche d'âge quinquennal (voir ageq)
    'men'
    '''
    age_en_mois = self.split_by_roles(age_en_mois_holder)

    ag1 = 0
    nb = 0
    for agm in age_en_mois.itervalues():
        age = floor(agm / 12)
        nb += (ag1 <= age) & (age <= (ag1 + 4))
    return nb


def _cohab(self, quimen_holder):
    '''
    Indicatrice de vie en couple
    'men'
    '''
    quimen = self.filter_role(quimen_holder, role = CREF)

    return quimen == 1


def _act_cpl(self, activite_holder, cohab):
    '''
    Nombre d'actifs parmi la personne de référence et son conjoint
    'men'
    '''
    activite = self.split_by_roles(activite_holder, roles = [PREF, CREF])

    return 1 * (activite[PREF] <= 1) + 1 * (activite[CREF] <= 1) * cohab


def _act_enf(self, activite_holder):
    '''
    Nombre de membres actifs du ménage autre que la personne de référence ou son conjoint
    'men'
    '''
    activite = self.split_by_roles(activite_holder, roles = ENFS)

    res = 0
    for act in activite.itervalues():
        res += 1 * (act <= 1)
    return res


def _nb_act(act_cpl, act_enf):
    '''
    Nombre de membres actifs du ménage
    'men'
    '''
    return act_cpl + act_enf


# def _cplx(typmen15):
def _cplx(self, quifam_holder, quimen_holder, age_holder):
    """
    Indicatrice de ménage complexe
    'men'

    Un ménage est complexe si les personnes autres que la personne de référence ou son conjoint ne sont pas enfants.
    """
    age = self.split_by_roles(age_holder, roles = ENFS)
    quifam = self.split_by_roles(quifam_holder, roles = ENFS)
    quimen = self.split_by_roles(quimen_holder, roles = ENFS)

    # TODO problème avec les ENFS qui n'existent pas: leur quifam = 0
    # On contourne en utilisant le fait que leur quimen = 0 également
    res = 0
    from itertools import izip
    for quif, quim, age_i in izip(quifam.itervalues(), quimen.itervalues(), age.itervalues()):
        res += 1 * (quif == 0) * (quim != 0) + age_i > 25

    return (res > 0.5)
    # En fait on ne peut pas car on n'a les enfants qu'au sens des allocations familiales ...
    # return (typmen15 > 12)


def _typmen15(nbinde, cohab, act_cpl, cplx, act_enf):
    '''
    Type de ménage en 15 modalités
    1 Personne seule active
    2 Personne seule inactive
    3 Familles monoparentales, parent actif
    4 Familles monoparentales, parent inactif et au moins un enfant actif
    5 Familles monoparentales, tous inactifs
    6 Couples sans enfant, 1 actif
    7 Couples sans enfant, 2 actifs
    8 Couples sans enfant, tous inactifs
    9 Couples avec enfant, 1 membre du couple actif
    10 Couples avec enfant, 2 membres du couple actif
    11 Couples avec enfant, couple inactif et au moins un enfant actif
    12 Couples avec enfant, tous inactifs
    13 Autres ménages, 1 actif
    14 Autres ménages, 2 actifs ou plus
    15 Autres ménages, tous inactifs
    'men'
    '''
    res = 0 + (cplx == 0) * (
            1 * ((nbinde == 1) & (cohab == 0) & (act_cpl == 1)) +  #  Personne seule active
            2 * ((nbinde == 1) & (cohab == 0) & (act_cpl == 0)) +  # Personne seule inactive
            3 * ((nbinde > 1) & (cohab == 0) & (act_cpl == 1)) +  # Familles monoparentales, parent actif
            4 * ((nbinde > 1) & (cohab == 0) & (act_cpl == 0) & (act_enf >= 1)) +  # Familles monoparentales, parent inactif et au moins un enfant actif
            5 * ((nbinde > 1) & (cohab == 0) & (act_cpl == 0) & (act_enf == 0)) +  # Familles monoparentales, tous inactifs
            6 * ((nbinde == 2) & (cohab == 1) & (act_cpl == 1)) +  # Couples sans enfant, 1 actif
            7 * ((nbinde == 2) & (cohab == 1) & (act_cpl == 2)) +  # Couples sans enfant, 2 actifs
            8 * ((nbinde == 2) & (cohab == 1) & (act_cpl == 0)) +  # Couples sans enfant, tous inactifs
            9 * ((nbinde > 2) & (cohab == 1) & (act_cpl == 1)) +  # Couples avec enfant, 1 membre du couple actif
            10 * ((nbinde > 2) & (cohab == 1) & (act_cpl == 2)) +  # Couples avec enfant, 2 membres du couple actif
            11 * ((nbinde > 2) & (cohab == 1) & (act_cpl == 0) & (act_enf >= 1)) +  # Couples avec enfant, couple inactif et au moins un enfant actif
            12 * ((nbinde > 2) & (cohab == 1) & (act_cpl == 0) & (act_enf == 0))  # Couples avec enfant, tous inactifs
                           ) + (cplx == 1) * (
            13 * (((act_cpl + act_enf) == 1)) +  # Autres ménages, 1 actif
            14 * (((act_cpl + act_enf) > 1)) +  # Autres ménages, 2 actifs ou plus
            15 * (((act_cpl + act_enf) == 0)))  # Autres ménages, tous inactifs

#    ratio = (( (typmen15!=res)).sum())/((typmen15!=0).sum())
    # print ratio  2.7 % d'erreurs enfant non nés et erreur d'enfants
    return res
