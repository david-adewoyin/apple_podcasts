# Apple podcasts :star: 
The scrapper was built using Python and Playwright :heart:


This is a web scrapping project where podcasts and user reviews were scrapped from the apple podcasts. The purpose of this project is to build a scrapper 
that can be use to collect data and build a dataset for data analysis and machine learning applications such as sentiment analysis and recommendation systems :computer:.

A small dataset is provided consisting of:
  - `2000+` podcasts data.
  - And over `500k` user reviews across the podcasts.

## Running the scrapper:
The scrapper was built using Python and Playwright, with Postgres being the database used, the code is modular enough that you can replace the database with anything you want. Follow this link in order to set up [Playwright]("https://playwright.dev/python/docs/intro")
1. add required dependencies:  
 `pip install psycopg2`    
2. Add a `Config.ini` file and add the details below for your specific postgres connection.
```
 [Database]
 port = '5432'
 password = 'postgres'
 username = 'postgres'
 hostname = 'localhost'
 database = 'podcasts'
 ```
 3. Finally run the scrapper:
 `python scrapper.py`
 

## Data Parsed:
Starting from the top chart page, top podcasts were parsed and subsequent podcasts were parsed from the category page and related podcasts that can be followed from the page.The following is an example of a data parsed from a podcast.
```
{
  "id" : 'id1647910854,
  "name" : 'Rachel Maddow Presents: Ultra',
  "url" : 'https://podcasts.apple.com/us/podcast/rachel-maddow-presents-ultra/id1647910854...',
  "studio" : 'MSNBC',
  "category" :"News",
  "episode_count" : 5,
  "avg_rating" : 4.8,
  "total_ratings":14900,
  "description":'Sitting members of Congress aiding and abetting a plot to overthrow the government. Insurrectionists criminally charged with plotting to end American democracy for good. Justice Department prosecutors under crushing political pressure. Rachel Maddow Presents: Ultra is the all-but-forgotten true story of good...'
}
```
The following is an example of a review:
```
{
  "id" : 3,
  "podcasts_id" : 'id1647910854',
  "username" : 'Pandora's Abyss',
  "review_title" : 'Thank you for bringing this to light!',
  "review" :"I say this has happened and people look at me as if I am crazy! This podcast is done exceptionally well!",
  "rating" : 5,
  "date" : "2022-10-28",
}
```
