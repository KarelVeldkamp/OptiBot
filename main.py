import yaml
import tweepy
import openai
from newsapi.newsapi_client import NewsApiClient
import datetime
import string
import time


def string_cleaner(str):
    """
    Helper function that removes interpunction and converts to lowerase
    :param string: a string
    :return: a cleaned string
    """
    # convert to lowercase
    result = str.lower()
    # remove interpunction
    result = result.translate(str.maketrans('', '', string.punctuation))
    return result


class OptiBot():
    def __init__(self, news_url, creds):

        self.news_url = news_url

        # initialize newsapi client
        self.news_client = NewsApiClient(api_key=creds['newsapi']['key'])

        # initialize twitter client
        self.twitter_client = tweepy.Client(
            consumer_key=creds['twitter']['key'],
            consumer_secret=creds['twitter']['secret'],
            access_token=creds['twitter']['access_token'],
            access_token_secret=creds['twitter']['access_token_secret']
        )

        # initialize openai api client
        openai.organization = creds['openai']['organization']
        openai.api_key = creds['openai']['api_key']

    def read_headlines(self, n):
        """
        reads headlines from the website provided when initalizing the model
        :return: a list of headlines
        """
        now = datetime.datetime.now()
        today = str(now.date())

        articles = self.news_client.get_everything(sources='bbc-news',
                                          from_param=today,
                                          to=today,
                                          language='en',
                                          sort_by='relevancy',
                                          page=1)['articles']

        #headlines = [a['title'] for a in articles][:n]

        return articles[:n]

    def generate_tweet(self, articles):
        """
        Generate tweet using GPT-3
        :param headlines: list of news headlines
        :return: string to tweet to Twitter
        """

        headlines = [a['title'] for a in articles]
        prompt = 'Write an optimistic and funny tweet mentioning at least one of these headlines: \n\n'
        prompt += "\n".join(headlines)

        nchar = 1e9
        i = 0
        while nchar > 280:
            i += 1
            print(f'Attempt {i}')
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                temperature=0.8,
                max_tokens=90,
                n=1
            )
            text = response['choices'][0]['text']
            nchar = len(text)

        return text

    def find_mentioned_headlines(self, tweet, articles):
        """
                Generate tweet using GPT-3
                :param headlines: list of news headlines
                :return: string to tweet to Twitter
                """
        headlines = [a['title'] for a in articles]
        prompt = 'below is a tweet and a list of headlines. ' \
                 'which of the headlines are explicitly mentioned in the tweet? \n\n'
        prompt += tweet
        prompt += "\n".join(headlines)

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.8,
            max_tokens=90,
            n=1
        )

        used_headlines = [string_cleaner(hl) for hl in response['choices'][0]['text'].splitlines()]

        urls = []
        for a in articles:
            if string_cleaner(a['title']) in used_headlines:
                urls.append(a['url'])

        return urls

    def tweet(self, text, reply_id=None):
        """
        posts a tweet to Twitter.
        :param text: text to post
        :param reply_id: tweet id to reply to
        """
        response = self.twitter_client.create_tweet(text=text, in_reply_to_tweet_id=reply_id)
        return response[0]['id']

if __name__ == "__main__":
    with open("./credentials.yml", "r") as f:
        creds = yaml.safe_load(f)

    bot = OptiBot('https://en.wikinews.org/wiki/Main_Page', creds)

    headlines = bot.read_headlines(25)
    generated_tweet = bot.generate_tweet(headlines)
    urls = bot.find_mentioned_headlines(generated_tweet, headlines)
    id = bot.tweet(generated_tweet)
    for url in urls:
        time.sleep(10)
        bot.tweet(url, id)
