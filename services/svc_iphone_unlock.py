"""
iPhone Unlock Services (sickw)
"""
from services.sickw_base import SickwService
from services import register


@register(98)
class UkO2TescoClean(SickwService):
    service_id = 98

@register(127)
class UkVodafoneClean(SickwService):
    service_id = 127

@register(111)
class UsaCspireClean(SickwService):
    service_id = 111

@register(95)
class CanadaTelusClean(SickwService):
    service_id = 95

@register(126)
class JapanAuKddiClean(SickwService):
    service_id = 126

@register(97)
class UkEeOrangePremium(SickwService):
    service_id = 97

@register(52)
class JapanSoftbankClean(SickwService):
    service_id = 52

@register(113)
class EmeaServicePremium(SickwService):
    service_id = 113

@register(116)
class JapanNttDocomoClean(SickwService):
    service_id = 116

@register(69)
class RomaniaOrangePremium(SickwService):
    service_id = 69

@register(50)
class PhilippinesGlobeClean(SickwService):
    service_id = 50

@register(71)
class RomaniaVodafonePremium(SickwService):
    service_id = 71

@register(51)
class UsaAttClean(SickwService):
    service_id = 51

@register(96)
class CanadaFidoRogers(SickwService):
    service_id = 96

@register(137)
class AustriaA1Premium(SickwService):
    service_id = 137

@register(234)
class UsaAttSoldDate60(SickwService):
    service_id = 234

@register(53)
class UsaCricketClean(SickwService):
    service_id = 53

@register(138)
class AustriaA1OutOfContract(SickwService):
    service_id = 138

@register(159)
class IrelandHutchisonPremium(SickwService):
    service_id = 159

@register(132)
class ClaroIphone14(SickwService):
    service_id = 132

@register(142)
class ClaroIphone15(SickwService):
    service_id = 142

@register(135)
class ClaroUpToIphone13(SickwService):
    service_id = 135
