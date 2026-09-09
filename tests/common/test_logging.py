from apps.common.logging import mask_sensitive_data


def test_mask_sensitive_data():
    event_dict = {
        "event": "user_login",
        "phone": "+998901234567",
        "password": "secretpassword",
        "nested": {
            "token": "abc.def.ghi",
            "access": "secret_access",
            "authorization": "Bearer token",
            "list": [
                {"refresh": "refresh_token"}
            ]
        },
        "safe_key": "safe_value"
    }

    masked = mask_sensitive_data(None, "info", event_dict)

    assert masked["phone"] == "+99890***4567"
    assert masked["password"] == "***"
    assert masked["nested"]["token"] == "***"
    assert masked["nested"]["access"] == "***"
    assert masked["nested"]["authorization"] == "***"
    assert masked["nested"]["list"][0]["refresh"] == "***"
    assert masked["safe_key"] == "safe_value"
    assert masked["event"] == "user_login"
