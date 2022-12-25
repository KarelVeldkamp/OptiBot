import yaml
import tweepy
import openai
import requests
from bs4 import BeautifulSoup


class OptiBot():
    def __init__(self, news_url, creds):

        self.news_url = news_url

        # initialize twitter client
        self.client = tweepy.Client(
            consumer_key=creds['twitter']['key'],
            consumer_secret=creds['twitter']['secret'],
            access_token=creds['twitter']['access_token'],
            access_token_secret=creds['twitter']['access_token_secret']
        )

        # initialize openai api client
        openai.organization = creds['openai']['organization']
        openai.api_key = creds['openai']['api_key']

    def read_headlines(self):
        """
        reads headlines from the website provided when initalizing the model
        :return: a list of headlines
        """
        # scrape headlines from the url
        response = requests.get(self.news_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.find('body').find_all('h3')
        # add text to list
        headlines = []
        for e in elements:
            headlines.append(e.text)

        return headlines

    def generate_tweet(self, headlines):
        """
        Generate tweet using GPT-3
        :param headlines: list of news headlines
        :return: string to tweet to Twitter
        """
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
                max_tokens=100,
                n = 1
            )
            text = response['choices'][0]['text']
            nchar = len(text)

        print(text)
        return text

    def tweet(self, text):
        """
        posts a tweet to Twitter.
        :param text: text to post
        """
        self.client.create_tweet(text=text)


if __name__ == "__main__":
    with open("./credentials.yml", "r") as f:
        creds = yaml.safe_load(f)

    bot = OptiBot('https://www.bbc.com/news/world', creds)

    headlines = bot.read_headlines()
    generated_tweet = bot.generate_tweet(headlines)
    bot.tweet(generated_tweet)