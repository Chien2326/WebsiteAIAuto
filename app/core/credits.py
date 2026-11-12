"""Server-side credit prices. Never accept a cost supplied by the browser.

Prices roughly follow provider cost: a short video costs far more Pollen than
an image, and website copy is a single cheap text completion.
"""

IMAGE_CREDITS_PER_IMAGE = 1
VIDEO_CREDITS_PER_SECOND = 2
WEBSITE_CREDITS = 2


def image_cost(quantity: int) -> int:
    return IMAGE_CREDITS_PER_IMAGE * quantity


def video_cost(duration_seconds: int) -> int:
    return VIDEO_CREDITS_PER_SECOND * duration_seconds


def website_cost() -> int:
    return WEBSITE_CREDITS


def public_credit_prices() -> dict[str, int]:
    return {
        "image_per_image": IMAGE_CREDITS_PER_IMAGE,
        "video_per_second": VIDEO_CREDITS_PER_SECOND,
        "website": WEBSITE_CREDITS,
    }
