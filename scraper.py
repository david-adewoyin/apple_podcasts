import logging
import time
import traceback
from database import DatabaseStore
from podcast_model import Podcast, UserReview
from playwright.sync_api import sync_playwright, BrowserContext
from utils import intercept_route, parse_id_from_url, parse_num, parse_review_from_page
import configparser

# DEFAULT CONFIGURATION
MAX_REVIEWS_COUNT = 500
MAX_PODCASTS_COUNT =30000

PODCASTS_PARSED = []

PODCASTS_QUEUE =[]  # list to hold podcasts not yet visited and parsed
PODCAST_CATEGORY_NAMES = set([]) ## list to store category names


def parse_top_podcast_from_cat_page(context: BrowserContext, category_link):
    """
    parse the top podcasts from the given category url
    """

    page = context.new_page()
    page.route("**/*", intercept_route)
    page.goto(category_link)

    section_selector = page.query_selector('div.l-row')
    podcasts_selector = section_selector.query_selector_all('a.we-lockup')

    for item in podcasts_selector:
        url = item.get_attribute('href')
        name = item.query_selector('.we-lockup__title').inner_text().strip()
        studio = item.query_selector(
            '.we-lockup__subtitle').inner_text().strip()
        id = parse_id_from_url(url)        
        pod = Podcast(name=name, url=url, studio=studio,id=id)
        if pod.name not in PODCASTS_PARSED:
            if pod not in PODCASTS_QUEUE:
                PODCASTS_QUEUE.append(pod)

    page.close()

def populate_queue(context:BrowserContext,podcast:Podcast):
    """
    populate queue from the category page and the see other podcasts section of a podcasts
    """
    page = context.new_page()  
    try:
        page.route("**/*", intercept_route)
        page.goto(podcast.url, wait_until='domcontentloaded', timeout=10_000)
        
        page.wait_for_selector('a.section__nav__see-all-link')
        parse_like_list(page)

        header_selector = page.query_selector('header.product-header')
        category_name = header_selector.query_selector(
            'li.inline-list__item').inner_text().strip()
            
        category_link = page.query_selector('a#ember12').get_attribute("href")
        category_link = 'https://podcasts.apple.com'+category_link
        
        if category_name not in PODCAST_CATEGORY_NAMES:
            parse_top_podcast_from_cat_page(context, category_link)
            # Add category to the list of categories
            PODCAST_CATEGORY_NAMES.add(category_name)
    except Exception as e:

        raise e
    finally:
        page.close()

def fetch_podcast_and_reviews(context: BrowserContext, podcast: Podcast):
    """
    Fetch reviews from the podcast page
    Returns:(Podcast,[UserReview])
    """
    
    page = context.new_page()
    try:
        print(podcast.name)
        page.route("**/*", intercept_route)
        page.goto(podcast.url, wait_until='domcontentloaded', timeout=60_000)
    
        header_selector = page.query_selector('header.product-header')
        try:
            studio = header_selector.query_selector('a.link').inner_text().strip()
            podcast.studio = studio
        except Exception as e:
            logging.error(f"unable to parse studio from :{podcast.name}")
    
        category_name = header_selector.query_selector(
            'li.inline-list__item').inner_text().strip()
        avg_rating = page.query_selector(
            '.we-customer-ratings__averages__display').inner_text().strip()
        episodes = page.query_selector(
            '.product-artwork__caption p').inner_text().strip().split()[0]
        description = page.query_selector(
            '.product-hero-desc__section p').inner_text().strip()
        total_rating = page.query_selector(
            'div.we-customer-ratings__count').inner_text().strip()
        total_rating = parse_num(total_rating.split()[0].lower())
    
       
        podcast.avg_rating = avg_rating
        podcast.category = category_name
        podcast.description = description
        podcast.total_episodes = int(episodes.replace(',',''))
        podcast.total_ratings = total_rating
    
        page.wait_for_selector('a.section__nav__see-all-link')
    
        # parse you might also like list
        parse_like_list(page)
    
        # get podcast category link
        category_link = page.query_selector('a#ember12').get_attribute("href")
        category_link = 'https://podcasts.apple.com'+category_link
    
        # fetch and parse category if it has not being passed before
        if category_name not in PODCAST_CATEGORY_NAMES:
            parse_top_podcast_from_cat_page(context, category_link)
            # Add category to the list of categories
            PODCAST_CATEGORY_NAMES.add(category_name)
    
        # click the see all reviews button
        page.wait_for_selector('a#ember5', timeout=10_000).click()
        reviews = parse_review_from_reviews_page(page)
        PODCASTS_PARSED.append(podcast.name)
        page.close()
        return (podcast, reviews)
    except Exception as e:
        page.close()
        raise e
        


def parse_review_from_reviews_page(page):
    """
    Parse User review from reviews Page
    Input: Page
    Returns : returns a list of user reviews list[UserReview]
    """
    reviews = []

    rating = page.query_selector(
        'div.we-customer-ratings__count').inner_text().strip()
    rating = rating.split()[0].lower()
    rating = parse_num(rating)

    feed = page.query_selector('div[role=feed]')

    # counter to count current review parsed
    current_review_counter = [0]
    max_review_number = min(rating, MAX_REVIEWS_COUNT)

    reviews_selector = feed.query_selector_all('div.we-customer-review')
    for item in reviews_selector:
        user_review = parse_review_from_page(item)
        reviews.append(user_review)
        current_review_counter[0] = current_review_counter[0]+1

    # fetch other reviews from the network as it loads
    page.on("response", lambda x: parse_review_from_network(
        x, current_review_counter, reviews))

    # keep fetching new reviews while the number is less than expected reviews needed
    # timeout after 1 minute
    timeout = time.time() + 60*1
    while current_review_counter[0] < max_review_number:
        page.mouse.wheel(0, 10)
        if time.time() > timeout:
            break

    return reviews


def parse_review_from_network(response, current, reviews):
    """
    Handler to parse reviews from the network
    """
    try:
        res = response.json()
        data = res['data']
        for item in data:
            podcast = item['attributes']

            date = podcast['date']
            review = podcast['review']
            username = podcast['userName']
            title = podcast['title']
            rating = podcast['rating']
            user_review = UserReview(
                username=username, date=date, review=review, title=title, rating=rating)
            reviews.append(user_review)
            if(current[0]%50==0):
                print("current_count",current[0])
            current[0] = current[0] + 1
    except Exception as e:
        return


def parse_like_list(page):
    """
    Parse the 'see other section' at the bottom of a podcast page
    """
    selector = page.query_selector_all('a.we-lockup.targeted-link')
    for item in selector:

        url = item.get_attribute('href')
        name = item.query_selector('.we-lockup__title').inner_text().strip()
        id = parse_id_from_url(url)
        pod = Podcast(name=name, url=url,id=id)

        if pod.name not in PODCASTS_PARSED:
            if pod not in PODCASTS_QUEUE:
                PODCASTS_QUEUE.append(pod)


def main(store: DatabaseStore):

    with sync_playwright() as p:
        current_podcasts_count = 0
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        homepage = context.new_page()

        homepage.route("**/*", intercept_route)
        print("starting application ..........")
        homepage.goto('https://www.apple.com/apple-podcasts/',
                      wait_until='domcontentloaded', timeout=10_000)

        homepage.click("#tab-gallery-top-charts-trigger")

        top_charts = homepage.query_selector('div.top-charts')
        top_charts_podcast = top_charts.query_selector_all(
            'ul.marquee-list:first-child li.marquee-item')

        for item in top_charts_podcast:
            url = item.query_selector('a.marquee-link').get_attribute('href')
            title = item.query_selector('p.show-title').inner_text().strip()

            id = parse_id_from_url(url)
            podcast = Podcast(name=title, url=url,id = id)
            
            
            if podcast.name in PODCASTS_PARSED:
                continue  # continue if podcast details has already been parsed
            try:
                logging.info(f"Fetching podcast:{podcast.name}")
                podcast, reviews = fetch_podcast_and_reviews(context, podcast)
                store.insert_podcast(podcast)
                store.insert_reviews(podcast.id, reviews)
                current_podcasts_count += 1
             
            except Exception as e:
                traceback.print_exc()
                logging.error(e)
                
        queue_count = 0
        print("The podcast queues ",len(PODCASTS_QUEUE))
        # fetch remaining podcasts
        while queue_count < len(PODCASTS_QUEUE):
            print(f"Total podcasts parsed : {current_podcasts_count}")
            if(current_podcasts_count > MAX_REVIEWS_COUNT):
                break
            podcast = PODCASTS_QUEUE[queue_count]
            if podcast.name in PODCASTS_PARSED:
                queue_count+=1 #increment queue count
                continue 
            try:
                print(f"Fetching podcast:{podcast.name} remaining:{len(PODCASTS_QUEUE) - queue_count}, current:{current_podcasts_count}")
                podcast, reviews = fetch_podcast_and_reviews(context, podcast)
                store.insert_podcast(podcast)
                store.insert_reviews(podcast.id, reviews)

                current_podcasts_count += 1
                queue_count+=1 #increment queue count
            except Exception as e:
                queue_count+=1 #increment queue count
                current_podcasts_count += 1
                logging.error(f"Error while fetching podcast in queue {e}")

        print(f"Total podcasts parsed : {current_podcasts_count}")
        logging.info(f"Writing remaining unparsed podcast into file")
        #writing remaining podcasts that has not yet being parsed into file
        with open('unprocessed_podcasts.txt', 'w') as f:
            for line in PODCASTS_QUEUE:
                f.write(f"{line.name, line.url}\n")
        context.close()
        browser.close()


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    database_config = config['DATABASE']
    try:

        data_store = DatabaseStore.create_database_from_config(database_config)
        # fetch podcasts data from the database into list to afford proccessing again
        podcasts = data_store.fetch_podcasts()
        podcasts = [pod[0] for pod in podcasts]
        PODCASTS_PARSED = podcasts

        main(data_store)
        data_store.close()

    except Exception as e:
        logging.error("{e}")
        
 


