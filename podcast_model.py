class Podcast:
    def __init__(self, name: str, url: str,id:str, studio =None, category = None, total_episodes = None, description = None, avg_rating = None, total_ratings = None):
        self.id = id
        self.url = url
        self.name = name
        self.studio = studio
        self.category = category
        self.total_episodes = total_episodes
        self.avg_rating= avg_rating
        self.description = description
        self.total_ratings = total_ratings


class UserReview:
    def __init__(self, username, title, review, rating, date):
        self.username = username
        self.title = title
        self.review = review
        self.rating = rating
        self.date = date
