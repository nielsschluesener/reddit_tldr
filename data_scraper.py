import pandas as pd
import numpy as np
import praw
import re
import os.path

#Set up PRAW (Reddit scraper)
user_agent = 'tl;dr-scraper by /u/nschlsnr'
praw_info = []

# !important note!
# 'reddit_api_info.txt' contains the client id (14chr) as a first line and the secret key (24chr)
# in order to get both, create an account at https://www.reddit.com/prefs/apps 
# !important note!
with open('reddit_api_info.txt','r') as txt:
    for line in txt:
        praw_info.append(line.rstrip())

reddit = praw.Reddit(
    client_id = praw_info[0],
    client_secret = praw_info[1],
    user_agent = user_agent
)
print('PRAW intialized.')

#Load existing data or create new dataset if none exists
if os.path.isfile('my_reddit_data.pkl'):
    df = pd.read_pickle('my_reddit_data.pkl')
    posts = df.values.tolist()
    
    print(f'Existing dataset with {len(posts)} items loaded.')
else:
    posts = []
    print('New, empty dataset created.')

#Search for posts from the defined subreddits that are not in the dataset yet
if len(posts) != 0:
    old_posts = np.array(posts)[:,0]
else:
    old_posts = []

new_posts = []
subreddits_monitored = ['relationships']

for sr in subreddits_monitored:
    sr_posts = []
    for p in reddit.subreddit(sr).hot(limit = None):
        if p.id not in old_posts:
            sr_posts.append([p.id, p.subreddit, p.title, p.selftext, 'tldr-placeholder', p.url])

    print(f'Found {len(sr_posts)} new posts in subreddit: {sr}.')
    new_posts += sr_posts

print(f'Found {len(new_posts)} new posts across all subreddits monitored.')

#Look for TLDRs in the freshly scraped posts
pattern = r'TL[\W]*DR.*[\n]*.*'

no_tldrs = []
i = 0

for p in new_posts:
    pos = re.search(pattern, p[3], flags = re.IGNORECASE)

    if pos is None:
        no_tldrs.append(i)
        i += 1
        continue
    
    p[4] = pos.group()
    p[3] = p[3].replace(p[4], '')
    i += 1

new_posts = np.delete(new_posts, no_tldrs, axis = 0)

print(f'Found {len(new_posts)} TLDRs.')
print(f'Discarded {i - len(new_posts)} observations not matching the defined pattern.')

#Add fresh data to existing dataset
if len(posts) == 0:
    posts = new_posts
elif len(posts) > 0:
    posts = np.concatenate((posts, new_posts), axis=0)

df = pd.DataFrame(posts, columns = ['id', 'subreddit', 'title', 'story', 'tldr', 'url'])

print(f'Concatenated old with new dataset, new dataset size is: {len(posts)} observations.')

#Save dataset
df.to_pickle('my_reddit_data.pkl', protocol = 4)
print('Dataset saved as \'my_reddit_data.pkl\'')