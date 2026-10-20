"""
Status Check Services (sickw)
"""
from services.sickw_base import SickwService
from services import register


@register(65)
class AttUsaStatusUnlock(SickwService):
    """AT&T USA STATUS & UNLOCK"""
    service_id = 65


@register(16)
class TMobileUsaStatus(SickwService):
    """T-MOBILE USA STATUS - PRO"""
    service_id = 16


@register(21)
class CricketUsaStatus(SickwService):
    """CRICKET USA STATUS - PRO"""
    service_id = 21


@register(232)
class VerizonUsaStatus(SickwService):
    """VERIZON USA STATUS - PRO"""
    service_id = 232


@register(230)
class XfinityUsaStatus(SickwService):
    """XFINITY USA STATUS - PRO"""
    service_id = 230


@register(231)
class CspireUsaStatus(SickwService):
    """CSPIRE USA STATUS - PRO"""
    service_id = 231


@register(220)
class TracfoneUsaStatus(SickwService):
    """TRACFONE USA STATUS - PRO"""
    service_id = 220


@register(6)
class WwBlacklistPro(SickwService):
    """WW BLACKLIST STATUS - PRO"""
    service_id = 6


@register(54)
class WwBlacklist(SickwService):
    """WW BLACKLIST STATUS"""
    service_id = 54


@register(24)
class BrazilBlacklist(SickwService):
    """BRAZIL BLACKLIST STATUS"""
    service_id = 24


@register(20)
class KoreaBlacklist(SickwService):
    """KOREA BLACKLIST STATUS"""
    service_id = 20


@register(32)
class JapanBlacklist(SickwService):
    """JAPAN BLACKLIST STATUS"""
    service_id = 32


@register(31)
class AustraliaBlacklist(SickwService):
    """AUSTRALIA BLACKLIST STATUS"""
    service_id = 31
