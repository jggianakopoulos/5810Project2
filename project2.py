import json
import tweepy as tw
import pandas as pd
import re
import emoji as em
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords


def processTweets(search, date, count, main_location, location_aliases, colors):
	# Read credentials from a json file
	with open('twittercredentials.json') as f:
		credentials = json.load(f)

	auth = tw.OAuthHandler(credentials["consumer_key"], credentials["consumer_secret"])
	auth.set_access_token(credentials["access_token"], credentials["access_token_secret"])

	# # https://developer.twitter.com/en/docs/twitter-api/v1/rules-and-filtering/overview/standard-operators
	api = tw.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
	search_words = search
	date = date

	tweets_data = tw.Cursor(api.search, q=search_words, date_since=date, until=date, lang='en',
							tweet_mode="extended").items(count)
	tweets = []
	locations = {main_location: 0, "Other": 0, "None": 0}
	all_tweets = ""
	for tweet in tweets_data:
		tweet_text = em.demojize(re.sub(r'http\S+', '', tweet.full_text)).replace("#", "").replace("\n", " ")
		# # https://pypi.org/project/textblob/
		tweet_textblob = TextBlob(em.demojize(tweet_text))
		sentiment = tweet_textblob.sentiment[0]

		all_tweets += tweet_text

		if tweet.user.location is not None and tweet.user.location.strip():
			location = em.demojize(tweet.user.location).lower()
			main = False

			for x in location_aliases:
				if x in location:
					main = True
					break

			if main:
				locations[main_location] += 1
			else:
				locations["Other"] += 1
		else:
			location = ""
			locations["None"] += 1

		tweets.append([sentiment, em.demojize(tweet.user.name), location, tweet.created_at])

	tweets_df = pd.DataFrame(data=tweets, columns=["sentiment", "user", "location", "date"])

	print("Sentiment mean:", tweets_df["sentiment"].mean())
	sentiment_df = tweets_df.apply(lambda x : 1
	             if x['sentiment'] > 0 else (-1 if x["sentiment"] < 0 else 0), axis = 1)

	sentiment_array = [0, 0, 0]
	for x in sentiment_df:
		if x == 1:
			sentiment_array[0] += 1
		elif x == -1:
			sentiment_array[1] += 1
		else:
			sentiment_array[2] += 1


	# WordCloud
	current_stopwords = set(stopwords.words('english'))
	current_stopwords.update(["Football", "Pittsburgh", "Washington", "Chiefs", "Broncos", "Steelers", "Ravens", "Chiefs", "NFL", "Week", "Browns"])
	tweet_wordcloud = WordCloud(stopwords=current_stopwords).generate(all_tweets)
	plt.imshow(tweet_wordcloud, interpolation='bilinear')
	plt.axis("off")
	plt.show()

	# Location Pie Chart
	fig1, ax1 = plt.subplots()
	ax1.pie(locations.values(), labels=locations.keys(), autopct='%1.1f%%', colors=colors, wedgeprops={'linewidth': 3})
	ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
	plt.show()


	#Sentiment bar graph
	plt.bar(["Positive", "Negative", "Neutral"], sentiment_array, color=colors)
	plt.xlabel("Sentiment")
	plt.ylabel("Number of Tweets")
	plt.show()

	return [tweets_df, locations]


steelers_df, steelers_locations = processTweets("#steelers -filter:retweets", "2020-12-05", 150, "Pennsylvania", ["pitt", ", pa", "pennsylvania"], ['#c9c753', '#4a4a49', '#c7c7c7'])
chiefs_df, chiefs_locations = processTweets("#chiefs -filter:retweets", "2020-12-05", 150, "Missouri", ["ks,", "kansas city", ", mo", ", ks", "kansas"], ["#fc1c03", '#c7c7c7', '#828181'])

print("STEELERS")
print(steelers_df)
print(steelers_locations)

print("\n\n\nCHIEFS")
print(chiefs_df)
print(chiefs_locations)

