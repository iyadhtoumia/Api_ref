"""Base class for all service implementations."""
from abc import ABC, abstractmethod


class BaseService(ABC):
    # Override in subclass if the service needs a serial (not IMEI)
    input_type: str = "imei"   # "imei" | "serial"

    @abstractmethod
    def run(self, identifier: str) -> dict:
        """
        Execute the service check.

        Args:
            identifier: IMEI or serial number depending on input_type

        Returns:
            {
                'success': bool,
                'result':  str,   # formatted text shown to user
                'raw':     dict,  # raw API response data
                'error':   str | None,
            }
        """
        ...
