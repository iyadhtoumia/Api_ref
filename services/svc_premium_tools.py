"""
Premium Tools & Services (sickw)
"""
from services.sickw_base import SickwService
from services import register


@register(94)
class MdmBypassIos26(SickwService):
    """MDM LOCK BYPASS (MAX IOS 26) - iPHONE/iPAD"""
    service_id = 94


@register(160)
class MdmBypassIos27(SickwService):
    """MDM LOCK BYPASS (IOS 27) - iPHONE/iPAD"""
    service_id = 160


@register(245)
class XiaomiMiAccountRemove(SickwService):
    """XIAOMI MI ACCOUNT REMOVE - EUROPE"""
    service_id = 245
