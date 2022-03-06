"""Bobiler.org'den monte yapici ile monte indirici

Calistirma komutlari:

```bash
virtualenv -p python3 env
source env/bin/activate
pip3 install -r requests bs4
python3 monte_cek.py --monteci=educatedear
```
"""
import argparse
import datetime
import json
import os
import logging
import requests
import sys
import time

# Third party deps.
from bs4 import BeautifulSoup


_BASE_MONTECI_PROFILE_URL = 'https://bobiler.org/{monteci}'
_BASE_MONTECI_URL = 'https://bobiler.org/Account/LoadNewContent?userId={author_id}&filter=0&currentTab=0&pageIndex={page}'

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Process input from user.')
parser.add_argument(
    '--monteci', dest='monteci', default='guldum', help='monte author')
args = parser.parse_args()


def fetch_html(url):
  response = requests.get(url)
  return response.text


def parse_html(html, should_save_db=True):
  extracted_posts = []
  soup = BeautifulSoup(html, 'html.parser')
  posts = soup.find_all('li', {'class': 'bobi-feed-monte'})
  logger.info('html icinden cikarabildigim postlarin sayisi: %s', len(posts))
  for post in posts: 
    monte_id = post.get('data-content-id')
    author_id = post.get('data-author-id')
    author_nick = post.get('data-author-nick')
    author_image_url = post.find('img', {'class': 'avatar'}).get('src')
    
    author_level = ''
    author_level_elem = post.find('span', {'class': 'userPopupBadge'})
    if author_level_elem:
      author_level = author_level_elem.get_text()

    post_headline_elem = post.find('div', {'class': 'bobi-feed-headline'})
    post_category = post_headline_elem.get('data-title')

    post_supirness = ''
    post_supirness_elem = post_headline_elem.find('span')
    if post_supirness_elem:
      post_supirness = post_supirness_elem.get_text()

    post_comment_count = '' 
    post_sokadens_count = ''
    post_stats_elem = post.find('div', {'class': 'bobi-comment-head'}) 
    if post_stats_elem:
      post_comment_and_sokadens_elems = post_stats_elem.find_all('span')
      if (post_comment_and_sokadens_elems and 
          len(post_comment_and_sokadens_elems) > 1):
        post_comment_count = post_comment_and_sokadens_elems[0].get_text()
        post_sokadens_count = post_comment_and_sokadens_elems[1].get_text()

    post_image_elem = post.find('figure', {'class': 'bobi-feed-image'})
    post_image_url = ''
    post_video_url = ''
    if post_image_elem:
      post_image_img_elem = post_image_elem.find('img')
      if not post_image_img_elem:
        logger.info('image cikmadi')
        continue
      post_image_url = post_image_img_elem.get('src')
      post_caption = post_image_elem.find('figcaption').get_text()
      video_elem = post_image_elem.find('video')
      if video_elem:
        post_video_url = video_elem.find('source').get('src')
    else:
      logger.info('asim pars')
      continue
    
    post_url = post.find(
        'div', {'class', 'bobi-feed-headline-left'}).find('a').get('href') 
      
    extracted_posts.append({
        'monte_id': monte_id,
        'author_id': author_id,
        'author_nick': author_nick,
        'author_level': author_level,
        'author_image_url': author_image_url,
        'post_category': post_category,
        'post_image_url': post_image_url,
        'post_video_url': post_video_url,
        'post_caption': post_caption,
        'post_url': post_url,
        'post_supirness': post_supirness,
        'post_comment_count': post_comment_count,
        'post_sokadens_count': post_sokadens_count,
    })

  return extracted_posts


def fetch_and_parse_all_pages(monteci=None, max_pages=10):
  logger.info('Su montecinin butun sayfalarini geziyorum %s', monteci)
  author_id = None

  # let's save this html somewhere to cache it further, 
  # so that we have a memory even though bobiler goes away.
  root_dir = f'html_{monteci}'

  # Check out the html cache if we already fetch this profile page.
  html = '' 
  monteci_profile_save_path = os.path.join(root_dir, monteci + '.html')
  if os.path.exists(monteci_profile_save_path):
    logger.info('profil htmli zaten indirilmis')
    with open(monteci_profile_save_path, 'r') as f:
      html = f.read()
  else:
    # No need to save.
    html = fetch_html(_BASE_MONTECI_PROFILE_URL.format(monteci=monteci),
                      should_save_db=False)

    # let's create if the root directory for the profile doesn't exist.
    if not os.path.exists(root_dir):
      os.makedirs(root_dir)

    with open(monteci_profile_save_path, 'w') as f:
      f.write(html)

  posts = parse_html(html)
  if not posts:
    logger.info('muhtemelen boyle bi monteci yok %s, exiting...', monteci)
    exit()
  # Hackily get the author id from one of the posts in the page.
  # Usually there are 10 in the page.
  author_id = posts[0]['author_id']
  logger.info('montecinin bobiler idsini buldum: %s as %s', monteci, author_id)

  # We are ready now, paginate.
  page = 1
  all_posts = []
  while True:
    page += 1 
    if page == max_pages:
      logger.info('bize ayrilan sayfanin sonuna geldim')
      break

    url = _BASE_MONTECI_URL.format(author_id=author_id, page=page)
    logger.info('=============indiriyorum url: %s', url)
    html = fetch_html(url)

    # Save to /html/ for main fetch ; 
    # save to /html/educatedear for per yazar fetch.
    html_save_path = f'html_{monteci}/bobiler_{page}.html'
    
    if os.path.exists(html_save_path):
      logger.info(f'{html_save_path} zaten inik, ineni kullaniyorum')
      html = ''
      with open(html_save_path, 'r') as f:
        html = f.read() 
    else:
      with open(html_save_path, 'w') as f:
        f.write(html)
    result = parse_html(html)
    if not result:
      logger.info('failed to parse html')
    all_posts += result
    # Don't overwhelm bobiler server.
    time.sleep(1)
  return all_posts 


def download_url(url, root_dir):
  logger.info('indiriyorum: %s', url)
  file_name_start_pos = url.rfind('/') + 1
  file_name = url[file_name_start_pos:]
 
  r = requests.get(url, stream=True)
  if r.status_code == requests.codes.ok:
    with open(os.path.join(root_dir, file_name), 'wb') as f:
      for data in r:
        f.write(data)


def download_post_media(monteci, post):
  image_url = post['post_image_url']
  video_url = post['post_video_url']
  media_root = f'media_{monteci}'

  media_dir = os.path.join(media_root, post['monte_id'])
  if os.path.exists(media_dir):
    logger.info('zaten bu medya inmis atliyorum: %s', media_dir)
    return (image_url, video_url) 

  # First create the dir.
  os.makedirs(media_dir)
  if image_url:
    download_url(image_url, media_dir)
  if video_url:
    download_url(video_url, media_dir)
  return (image_url, video_url) 


def download_sequential(monteci, posts):
  for counter, post in enumerate(posts):
    if counter % 1000 == 0:
      logger.info(f'indirmesi biten postlar: {counter} posts')
    download_post_media(monteci, post)
  logger.info('butun postlari indirdim galiba')


def main():
  ts = time.time()
  logger.info('baslangic: %s', ts)
  logger.info('Params: %s', args)
  all_posts = fetch_and_parse_all_pages(monteci=args.monteci, max_pages=3)
  open('debug.json', 'w').write(json.dumps(all_posts, indent=4))
  # exit()
  download_sequential(args.monteci, all_posts)
  logger.info('total calisma suresi: %s saniyes', (time.time() - ts))


if __name__ == '__main__':
  main()
  