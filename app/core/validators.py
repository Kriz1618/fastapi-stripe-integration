"""
Validators for application configuration
"""


def validate_stripe_key(key: str, key_type: str) -> str:
    """
    Validate Stripe keys

    Args:
        key: Key to validate
        key_type: Key type ("secret", "publishable", "webhook")

    Returns:
        str: The validated key

    Raises:
        ValueError: If the key is not valid
    """
    if key_type == "secret":
        if key == "sk_test_placeholder":
            raise ValueError(
                "STRIPE_SECRET_KEY must be configured with a real value from Stripe Dashboard"
            )
        if not (key.startswith("sk_test_") or key.startswith("sk_live_")):
            raise ValueError(
                "STRIPE_SECRET_KEY must start with 'sk_test_' or 'sk_live_'"
            )

    elif key_type == "publishable":
        if key == "pk_test_placeholder":
            raise ValueError(
                "STRIPE_PUBLISHABLE_KEY must be configured with a real value from Stripe Dashboard"
            )
        if not (key.startswith("pk_test_") or key.startswith("pk_live_")):
            raise ValueError(
                "STRIPE_PUBLISHABLE_KEY must start with 'pk_test_' or 'pk_live_'"
            )

    elif key_type == "webhook":
        if key == "whsec_placeholder":
            raise ValueError(
                "STRIPE_WEBHOOK_SECRET must be configured with a real value from Stripe Dashboard"
            )
        if not key.startswith("whsec_"):
            raise ValueError("STRIPE_WEBHOOK_SECRET must start with 'whsec_'")

    else:
        raise ValueError(f"Unknown key type: {key_type}")

    return key
