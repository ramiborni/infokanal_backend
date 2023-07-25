import requests_html


class Scraper:
    def __init__(self):
        # Initialize the HTML Session for the web scraper
        self.ses = requests_html.HTMLSession()

    def filter_article_body_source(self, article):
        # Function to determine which part of the article to scrape based on the source name
        source_name = article['feed_source_name']
        if source_name == "fetchrss.com":
            return article["data"]["description"]
        if source_name == "finansavisen.no":
            if "content" in article["data"]:
                return article["data"]["content"][0]['value']
            else:
                return article["data"]["link"]
        if source_name in ["grannar.no", "karmoynytt.no", "sunnhordland.no"]:
            return article["data"]["link"]
        if source_name == "h-avis.no":
            if "api:body" in article["data"]:
                return article["data"]["api:body"]
            else:
                return article["data"]["link"]

    def karmoynytt(self, url):
        # Function to scrape data from karmoynytt.no
        # Cookies are used here for handling sessions (if needed)
        cookies = {
            'PHPSESSID': 'nnhc5747n940mgovcphivg7fv2',
            'REMEMBERME': 'Qm9kb1xVc2VyQnVuZGxlXEVudGl0eVxDdXN0b21lcjpaV2RwYkM1dFlYSjBhVzR1YzI5c1ltVnlaMEJuYldGcGJDNWpiMjA9OjE3ODQ2MTM1Mjg6NjM1OTY0MTNlYmVjNWRlNmM4ZGZjODEyZDQ0MzZjN2RlYzRiMzI3ZGFlMWJhYWQ1ZTMzYWViYWMzYjY1NmE1Mw%3D%3D',
        }
        response = self.ses.get(url, cookies=cookies)

        if response.status_code == 200:
            html_content = response.html
            article = html_content.find('div.articleText', first=True)
            article.html = article.html.replace("""<advertising script>""", '')
            return article.text
        else:
            print(response.status_code, response.text)
            return "Failed to fetch the page."

    def h_avis(self, url):
        # Function to scrape data from h-avis.no
        # Cookies are used here for handling sessions (if needed)
        cookies = {
            'aid.session': 'qp3y99fbs3hvqk1ae534u6kqmhkaf0yxhqycv9dfwvazx4pmbvncc1lbqvgunce5cit1h56h1ydp3zjyufux1ofxuu8e7f9l6r7',
            'VSTOKEN': '75fd5f3550:1690417302:newspaper,subscription:ae632f18-a900-4fe0-96eb-a93c7f075ccd:h-avis:jupiter',
            'VSTOKEN2': '35aef9fe41:1690251703:::h-avis:jupiter',
            'amedia:visitid': '99935ad3-9f64-49f8-b2a8-f6665634fb12|1690246415334'
        }

        response = self.ses.get(url, cookies=cookies)

        if response.status_code == 200:
            html_content = response.html
            article = html_content.find('div.article-body', first=True)
            article.html = article.html.replace("""
            <div class="visible-xs spacing-both">
            <div class="adspot" style="">
            <!-- /22268814378/ARTICLE_BOARD_MOBILE-->
            <div class="ad-label" id="div-gpt-ad-1612264910531-0">
            <script>&#13;
                googletag.cmd.push(function() { googletag.display('div-gpt-ad-1612264910531-0'); });&#13;
              </script>
            </div>
            </div>
            </div>
            <div class="hidden-xs spacing-both">
            <div class="adspot" style="">
            <!-- /22268814378/ARTICLE_BOARD_DESKTOP-->
            <div class="ad-label" id="div-gpt-ad-1612446493384-0">
            <script>&#13;
                googletag.cmd.push(function() { googletag.display('div-gpt-ad-1612446493384-0'); });&#13;
              </script>
            </div>
            </div>
            </div>
            """, '')
            return article.text
        else:
            print(response.status_code, response.text)
            return "Failed to fetch the page."

    def no_auth(self, article):
        # Function to handle articles which don't need authentication
        return article


def choose_scraping_method(method_name, article_body):
    # Function to map the source name to the respective function for scraping
    scraper = Scraper()

    methods = {
        'karmoynytt.no': scraper.karmoynytt,
        'h-avis.no': scraper.h_avis,
        'fetchrss.com': scraper.no_auth,
        'grannar.no': scraper.no_auth,
        'finansavisen.no': scraper.no_auth,
        'sunnhordland.no': scraper.no_auth,
    }

    func = methods.get(method_name)

    if func:
        return func(scraper.filter_article_body_source(article_body))  # Executing the chosen function
    else:
        raise ValueError(f"Invalid method name: {method_name}")  # Raising error for invalid source name
