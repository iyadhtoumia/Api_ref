"""
Generic Unlock Services (sickw)
"""
from services.sickw_base import SickwService
from services import register


@register(57)
class UkO2Clean(SickwService):
    service_id = 57

@register(107)
class FranceBouygues(SickwService):
    service_id = 107

@register(104)
class CanadaVideotron(SickwService):
    service_id = 104

@register(115)
class HtcInternational(SickwService):
    service_id = 115

@register(125)
class SamsungEuropePremium(SickwService):
    service_id = 125

@register(134)
class SamsungUkIreland(SickwService):
    service_id = 134

@register(130)
class SamsungEuropeLimited(SickwService):
    service_id = 130
