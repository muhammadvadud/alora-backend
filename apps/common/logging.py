from typing import Any

MASKED_KEYS = {"token", "access", "refresh", "password", "authorization", "phone"}


def mask_sensitive_data(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """
    Log yozuvlaridagi maxfiy ma'lumotlarni maskalaydi (structlog processor).
    """

    def _mask(data: Any) -> Any:
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                if isinstance(k, str) and k.lower() in MASKED_KEYS:
                    if k.lower() == "phone" and isinstance(v, str) and len(v) >= 9:
                        # Masalan, +998901234567 -> +99890***4567
                        new_dict[k] = f"{v[:6]}***{v[-4:]}"
                    else:
                        new_dict[k] = "***"
                else:
                    new_dict[k] = _mask(v)
            return new_dict
        elif isinstance(data, list):
            return [_mask(item) for item in data]
        return data

    return _mask(event_dict)
