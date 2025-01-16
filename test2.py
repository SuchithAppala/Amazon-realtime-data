import requests
import pandas as pd
import pandas as pd
from nltk.tokenize import word_tokenize
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
import nltk
nltk.download('punkt_tab')

print('product details fetching...............')

url = "https://real-time-amazon-data.p.rapidapi.com/best-sellers"

querystring = {"category":"software","type":"BEST_SELLERS","page":"1","country":"US"}

headers = {
	"x-rapidapi-key": "e7979959c6msh35fdc1ac494a45ap1b7847jsn74865f28b32e",
	"x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
print(response.json())
software_products=response.json()['data']['best_sellers']
live_data=pd.DataFrame(software_products)
print(live_data)

live_asins=live_data['asin'].unique()






# List of ASINs
asin_list = live_asins

print('product reviews fetching.......................')
# Base URL and headers for the API
url = "https://real-time-amazon-data.p.rapidapi.com/product-reviews"
headers = {
	"x-rapidapi-key": "e7979959c6msh35fdc1ac494a45ap1b7847jsn74865f28b32e",
	"x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
}

# Initialize an empty DataFrame to store results
all_reviews_df = pd.DataFrame()
count =0
# Loop through the ASINs
for asin in asin_list:
    querystring = {
        "asin": asin,
        "country": "US",
        "sort_by": "TOP_REVIEWS",
        "star_rating": "ALL",
        "verified_purchases_only": "false",
        "images_or_videos_only": "false",
        "current_format_only": "false",
        "page": "1"
    }

    # Make the request
    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        # Parse the JSON response
        reviews_data = response.json()

        # Extract parameters and reviews
        asin_value = reviews_data.get("parameters", {}).get("asin")
        reviews = reviews_data.get("data", {}).get("reviews", [])

        # Convert reviews to DataFrame
        reviews_df = pd.DataFrame(reviews)

        # Add ASIN column to DataFrame
        reviews_df["asin"] = asin_value

        # Append to the main DataFrame
        all_reviews_df = pd.concat([all_reviews_df, reviews_df], ignore_index=True)
    else:
        print(f"Failed to fetch data for ASIN {asin}. Status code: {response.status_code}")
    count = count + 1
    if count == 2:
        break
# Display the resulting DataFrame
print(all_reviews_df)
print(all_reviews_df.info())
print('merging data....................')
# Perform an inner join on the 'asin' column
merged_df = pd.merge(all_reviews_df, live_data, on='asin', how='inner')


print('sentiment addition...................')
# Initialize the VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

def extract_top_contributing_words_unique(review):
    """
    Analyze the review to extract the compound score, sentiment label,
    and top unique contributing words by sentiment score.
    """
    # Get the compound score and overall sentiment
    sentiment_scores = analyzer.polarity_scores(review)
    compound = sentiment_scores['compound']
    if compound > 0.05:
        sentiment_label = "Positive"
    elif compound < -0.05:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"

    # Tokenize the review
    tokens = word_tokenize(review)

    # Score each token and filter by sentiment label
    word_scores = []
    for token in tokens:
        if not token.isalpha():  # Skip non-alphabetic tokens
            continue
        token_score = analyzer.polarity_scores(token)['compound']
        if sentiment_label == "Positive" and token_score > 0.05:
            word_scores.append((token, token_score))
        elif sentiment_label == "Negative" and token_score < -0.05:
            word_scores.append((token, token_score))

    # Sort words by their sentiment score and extract the top contributors
    top_words = [word for word, score in sorted(word_scores, key=lambda x: abs(x[1]), reverse=True)]

    # Remove duplicates while preserving order
    unique_top_words = list(dict.fromkeys(top_words))[:3]  # Extract up to 3 unique words

    return compound, sentiment_label, unique_top_words

# Apply the function to the DataFrame
merged_df[['sentiment', 'tags','sentiment_score']] = merged_df['review_comment'].apply(
    lambda x: pd.Series(extract_top_contributing_words_unique(x))
)
merged_df['category']='software'



print(merged_df.info())

