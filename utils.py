from urllib.parse import urlparse
from podcast_model import UserReview


BLOCK_RESOURCE_NAMES = [
    'adzerk',
    'analytics',
    'cdn.api.twitter',
    'doubleclick',
    'exelator',
    'facebook',
    'fontawesome',
    'google',
    'google-analytics',
    'googletagmanager',
]

BLOCK_RESOURCE_TYPES = [
    'beacon',
    'csp_report',
    'font',
    'image',
    'imageset',
    'media',
    'object',
    'texttrack',
]
def parse_id_from_url(url)->str:
    # returns the the podcast id from the url
    url = urlparse(url)
    url = url.path
    id = url.split("/")[-1]
    return id

def intercept_route(route, block_resource_types=BLOCK_RESOURCE_TYPES, block_resource_names=BLOCK_RESOURCE_NAMES):
    """intercept all requests and abort blocked ones"""
    if route.request.resource_type in BLOCK_RESOURCE_TYPES:
        #print(f'blocking background resource {route.request} blocked type "{route.request.resource_type}"')
        return route.abort()
    if any(key in route.request.url for key in BLOCK_RESOURCE_NAMES):
        #print( f"blocking background resource {route.request} blocked name {route.request.url}")
        return route.abort()
    return route.continue_()


def parse_review_from_page(item_selector) -> UserReview:
    user_rating = item_selector.query_selector(
        'figure.we-star-rating').get_attribute('aria-label').split()[0]
    username = item_selector.query_selector(
        '.we-customer-review__user').inner_text().strip()
    title = item_selector.query_selector(
        '.we-customer-review__title').inner_text().strip()
    review = item_selector.query_selector('.we-clamp').inner_text().strip()
    date = item_selector.query_selector(
        '.we-customer-review__date').inner_text().strip()
    return UserReview(
        date=date,
        title=title,
        review=review,
        username=username,
        rating=user_rating,
    )


def parse_num(value: str)->float:
    try:
        num = float(value)
        return num
    except ValueError:
        num = float(value[:-1])
        num = num * 1000
        return num

