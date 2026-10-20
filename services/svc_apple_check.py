"""
Apple Check Services (sickw)
Add new Apple check services here as they are enabled.
"""
from services.sickw_base import SickwService
from services import register


@register(105)
class AppleSoldByCountry(SickwService):
    """APPLE SOLD BY & COUNTRY INFO"""
    service_id = 105


@register(63)
class AppleGsxPremium(SickwService):
    """APPLE GSX PREMIUM DETAILS"""
    service_id = 63


@register(146)
class AppleGsxPremiumPromo(SickwService):
    """APPLE GSX PREMIUM - PROMO"""
    service_id = 146


@register(29)
class AppleReplacementsHistory(SickwService):
    """APPLE REPLACEMENTS HISTORY"""
    service_id = 29


@register(77)
class AppleGsxRepairEligibility(SickwService):
    """APPLE GSX REPAIR ELIGIBILITY"""
    service_id = 77


@register(68)
class AppleGsxCasesRepairs(SickwService):
    """APPLE GSX CASES & REPAIRS"""
    service_id = 68


@register(60)
class AppleIcloudIdHint(SickwService):
    """APPLE iCLOUD ID HINT"""
    service_id = 60


@register(219)
class ApplePartNumber(SickwService):
    """APPLE PART NUMBER - MPN"""
    service_id = 219


@register(103)
class IphoneCarrier(SickwService):
    """iPHONE CARRIER"""
    service_id = 103


@register(78)
class IphoneCarrierFmi(SickwService):
    """iPHONE CARRIER & FMI"""
    service_id = 78


@register(151)
class IphoneCarrierChimaera(SickwService):
    """iPHONE CARRIER & CHIMAERA DETECT"""
    service_id = 151


@register(61)
class IphoneCarrierFmiBlacklist(SickwService):
    """iPHONE CARRIER & FMI & BLACKLIST"""
    service_id = 61


@register(147)
class IphoneCarrierFmiBlacklistS2(SickwService):
    """iPHONE CARRIER & FMI & BLACKLIST - S2"""
    service_id = 147


@register(72)
class AppleCarrierMdmIcloudGsx(SickwService):
    """APPLE CARRIER + MDM & iCLOUD & GSX STATUS"""
    service_id = 72


@register(92)
class IphoneModelColorCapacity(SickwService):
    """iPHONE MODEL COLOR & CAPACITY"""
    service_id = 92


@register(12)
class ImeiSnConvert(SickwService):
    """IMEI ⇄ SN CONVERT"""
    service_id = 12


@register(26)
class AppleSerialInfo(SickwService):
    """APPLE SERIAL INFO"""
    service_id = 26


@register(3)
class IcloudOnOff(SickwService):
    """iCLOUD ON/OFF"""
    service_id = 3


@register(101)
class AppleActivationStatus(SickwService):
    """APPLE ACTIVATION STATUS"""
    service_id = 101


@register(88)
class AppleActivationStatusPro(SickwService):
    """APPLE ACTIVATION STATUS - PRO"""
    service_id = 88


@register(152)
class AppleWarrantyBySerial(SickwService):
    """APPLE WARRANTY STATUS - BY SERIAL"""
    service_id = 152


@register(85)
class AppleDemoDevices(SickwService):
    """APPLE DEMO DEVICES INFO"""
    service_id = 85


@register(81)
class AppleMdmStatus(SickwService):
    """APPLE MDM STATUS"""
    service_id = 81


@register(40)
class AppleMdmIcloudStatus(SickwService):
    """APPLE MDM & iCLOUD STATUS"""
    service_id = 40


@register(110)
class MacbookImacIcloud(SickwService):
    """MACBOOK & iMAC iCLOUD ON/OFF STATUS"""
    service_id = 110


@register(66)
class IphoneMacIcloudStatus(SickwService):
    """iPHONE & MAC iCLOUD CLEAN/LOST STATUS"""
    service_id = 66
