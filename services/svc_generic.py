"""
Generic Device Info Services (sickw)
"""
from services.sickw_base import SickwService
from services import register


@register(34)
class AsusInfo(SickwService):
    service_id = 34

@register(23)
class AcerInfo(SickwService):
    service_id = 23

@register(73)
class HonorInfo(SickwService):
    service_id = 73

@register(86)
class SparxInfo(SickwService):
    service_id = 86

@register(56)
class DoogeeInfo(SickwService):
    service_id = 56

@register(15)
class HuaweiInfo(SickwService):
    service_id = 15

@register(22)
class LenovoInfo(SickwService):
    service_id = 22

@register(43)
class KyoceraInfo(SickwService):
    service_id = 43

@register(80)
class SamsungInfo(SickwService):
    service_id = 80

@register(17)
class AlcatelInfo(SickwService):
    service_id = 17

@register(13)
class MotorolaInfo(SickwService):
    service_id = 13

@register(75)
class VivoIqooInfo(SickwService):
    service_id = 75

@register(42)
class GooglePixelInfo(SickwService):
    service_id = 42

@register(233)
class NothingPhoneInfo(SickwService):
    service_id = 233

@register(1)
class SamsungInfoPro(SickwService):
    service_id = 1

@register(203)
class BrandModelInfo(SickwService):
    service_id = 203

@register(87)
class UnityCellecorInfo(SickwService):
    service_id = 87

@register(37)
class SimIccidImsiInfo(SickwService):
    service_id = 37

@register(82)
class SamsungKnoxGuard(SickwService):
    service_id = 82

@register(55)
class ZteNubiaRedmagic(SickwService):
    service_id = 55

@register(45)
class ItelInfinixTecno(SickwService):
    service_id = 45

@register(153)
class XiaomiWarranty(SickwService):
    service_id = 153

@register(39)
class OppoOneplusRealme(SickwService):
    service_id = 39

@register(206)
class XiaomiMiLock(SickwService):
    service_id = 206
