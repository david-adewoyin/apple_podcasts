import psycopg2
from psycopg2 import Error
from psycopg2.extras import execute_batch
import logging

from podcast_model import Podcast, UserReview

class DatabaseStore:
    def __init__(self, user: str, password: str, host: str, port: str,database=None):
        try:
            self.connection = psycopg2.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database = database
            )

            cursor = self.connection.cursor()
            self.connection.autocommit = True
            # create a new database if id doesnt exists
            if database == None:
                create_database ='''
                create database podcasts
                '''
                cursor.execute(create_database)
                cursor.close()
                self.connection.close()

                self.connection =  psycopg2.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database = 'podcasts',
            )
                
            logging.info("Succesfully connected to postgres")
        except Exception as e:
            logging.error(f" Error while connecting to postgres: {e}")
            raise e
            
    @staticmethod
    def create_database_from_config(config):
        """
        Create and connect to a database from configuration
        """
        user = config['USER']
        host = config['HOST']
        password = config['PASSWORD']
        port = config['PORT']
        dbname = config['DBNAME']
        data_store = DatabaseStore(user=user, password=password,port=port, host=host, database=dbname)
        data_store.create_podcast_and_reviews_tables()

        return data_store
        
    def create_podcast_and_reviews_tables(self):
        cursor = self.connection.cursor()
        create_podcast_table = '''
        create table if not exists podcasts(
        id text primary key unique,
        name text not null,
        url text not null,
        studio text,
        category text,
        episode_count int,
        avg_rating float,
        total_ratings int,
        description text
        )   '''
        
        create_reviews_table = '''
        create table if not exists user_reviews(
        id serial primary key,
        podcast_id text REFERENCES podcasts(id) not null,
        username text not null,
        title text not null,
        review text not null,
        rating float not null,
        date date not null
        )
        '''
        try:
            cursor.execute(create_podcast_table)
            cursor.execute(create_reviews_table)
            self.connection.commit()
            cursor.close()
            logging.info("Podcast Table created")
        except Exception as e:
            logging.error(f" Error while connecting to postgres: {e}")
    
    def insert_podcast(self,podcast:Podcast):
        """
        Insert podcast information to a database
        Returns: Podcast id from database
        """

        cursor = self.connection.cursor()
        query ="""INSERT INTO podcasts(id,name,url,studio,category,episode_count,avg_rating,total_ratings,description)
             VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
        try:
            cursor.execute(query,(podcast.id,podcast.name,podcast.url,podcast.studio,podcast.category,podcast.total_episodes,podcast.avg_rating,podcast.total_ratings,podcast.description))
            self.connection.commit()

            logging.info("Successfully inserted podcast into database")
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
             logging.error(f" Error while inserting podcast : {e}")

    def insert_reviews(self,podcast_id:int,reviews):
        """
        Insert a list of reviews belonging to a podcast to a database
        """

        cursor = self.connection.cursor()
        query ="""INSERT INTO user_reviews(podcast_id,title,username,rating,review,date)
             VALUES(%s,%s,%s,%s,%s,%s)"""

        try:  
            reviews = [(podcast_id,review.title,review.username,review.rating,review.review,review.date) for review in reviews]
            execute_batch(cursor,query,reviews)
            self.connection.commit()

            logging.info("reviews inserted into database")
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
             logging.error(f" Error while inserting record : {e}")   
             
    def fetch_podcasts(self):
        """
        Insert a list of reviews belonging to a podcast to a database
        """

        cursor = self.connection.cursor()
        query ="""select name from podcasts"""
        try:  
            cursor.execute(query)
            lists = cursor.fetchall()
            
            self.connection.commit()

            
            cursor.close()
            return lists
        except (Exception, psycopg2.DatabaseError) as e:
             logging.error(f" Error while fetching record : {e}")   

    def close(self):
        # close the database connection
        self.connection.close()


