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
        if source_name == "NRK Siste nytt" or source_name == "NRK Rogaland":
            return article["data"]["link"]
        if source_name == 'aftenposten.no':
            return article["data"]["link"]
        if source_name == 'nettavisen.no':
            return article["data"]["link"]
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
            'VSTOKEN': '9f1c4dcd7d:1690808013:newspaper,subscription:ae632f18-a900-4fe0-96eb-a93c7f075ccd:h-avis:jupiter',
            'VSTOKEN2': '336d7b8480:1690642413:::h-avis:jupiter',
            'amedia:visitid': '99935ad3-9f64-49f8-b2a8-f6665634fb12|1690246415334',
            'daxsub': 'a_sub_status%3Dactive%26a_user_key%3De52cd9e2-8585-4c64-918c-217c5c6bb611',
            '__mbl': '61@{"u":[{"uid":"OwOtAEDyK7MK3zx2","ts":1689858229},1689948229]}',
            '_k5a': '61@{"u":[{"uid":"eSOb6Slsy40DKQaF","ts":1689858229},1689948229]}',
            'amedia:fpbid': '6b2f4111-b729-4a9d-ab02-7fe5eb9efd9b'
        }

        for attempt in range(2):  # Two attempts: first one and then a refresh

            response = self.ses.get(url, cookies=cookies)

            if response.status_code == 200:
                if response.html:
                    # Process the HTML content
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
                    # If the HTML is empty, refresh (make another request) and save cookies
                    print("HTML was empty, refreshing page.")
                    cookies = response.cookies
            else:
                print(response.status_code, response.text)
                return "Failed to fetch the page."

    def nrk(self, url):
        # Function to scrape data from nrk.no
        response = self.ses.get(url)
        if response.status_code == 200:
            html_content = response.html
            article = html_content.find('div.bulletin-text', first=True)
            return article.text

    def vg_no(self, url):
        # Function to scrape from vg.no
        response = self.ses.get(url)
        if response.status_code == 200:
            html_content = response.html
            article = html_content.find('article', first=True)
            article.html = article.html.replace("""
            <div role="region" class="hyperion-css-1jjqa7j"><div><div data-nosnippet="true" class="hyperion-css-kzdiax"><h2>Kortversjonen</h2><button aria-controls="summary-info" type="button" aria-label="Vis informasjon" class="hyperion-css-q17jg7"><svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="height:auto;width:var(--icon-size, var(--space-l))"><path fill-rule="evenodd" clip-rule="evenodd" d="M1 12C1 18.0751 5.92487 23 12 23C18.0751 23 23 18.0751 23 12C23 5.92487 18.0751 1 12 1C5.92487 1 1 5.92487 1 12ZM12 10C11.4477 10 11 10.4477 11 11V16C11 16.5523 11.4477 17 12 17C12.5523 17 13 16.5523 13 16V11C13 10.4477 12.5523 10 12 10ZM11 8C11 7.44772 11.4477 7 12 7C12.5523 7 13 7.44772 13 8C13 8.55228 12.5523 9 12 9C11.4477 9 11 8.55228 11 8Z" fill="var(--icon-color, currentColor)"></path></svg></button></div><div><div id="summary-details" aria-expanded="false" style="height:60px;overflow:hidden" class="hyperion-css-ddshmh"><span class="hyperion-css-11s3z4v"></span><ul class="hyperion-css-30kyl1" data-test-tag="list"><li class="hyperion-css-1y34876"><span>Artikkelen handler om den populære TV-serien «One Tree Hill», hva slags liv skuespillerne lever i dag og hvilke prosjekter de har jobbet med etter serien.</span></li><li class="hyperion-css-1y34876"><span>Chad Michael Murray spilte Lucas Scott. Han har senere vært med i flere TV-serier og filmer.</span></li><li class="hyperion-css-1y34876"><span>Sophia Bush, som spilte rollen som Brooke Davis, har også oppnådd suksess etter «One Tree Hill». Hun har vært med i serier som «Love, Victor» og «Deborah». I 2017 anklaget hun og 18 andre kvinner fra «One Tree Hill»-produksjonen serieskaper for seksuell trakassering og manipulasjon.</span></li><li class="hyperion-css-1y34876"><span>James Lafferty spilte Nathan Scott. Han har siden jobbet med flere filmer som skuespiller, produsent, regissør og manusforfatter.</span></li><li class="hyperion-css-1y34876"><span>Hilarie Burton, kjent som Peyton Sawyer, har etter serien vært med i TV-serier som «White Collar» og «Grey’s Anatomy».</span></li><li class="hyperion-css-1y34876"><span>Bethany Joy Lenz, som spilte Haley James, har også deltatt i flere TV-serier etter «One Tree Hill», inkludert «Grey’s Anatomy» og «Dexter».</span></li></ul></div></div></div><button type="button" aria-label="Vis sammendrag" aria-controls="summary-details" class="hyperion-css-1l2n4gy"><svg width="24px" height="24px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="height:auto;width:var(--icon-size, var(--space-l))"><path d="M3.29289 8.70711L11.2929 16.7071C11.6834 17.0976 12.3166 17.0976 12.7071 16.7071L20.7071 8.70711C21.0976 8.31658 21.0976 7.68342 20.7071 7.29289C20.3166 6.90237 19.6834 6.90237 19.2929 7.29289L12 14.5858L4.70711 7.29289C4.31658 6.90237 3.68342 6.90237 3.29289 7.29289C2.90237 7.68342 2.90237 8.31658 3.29289 8.70711Z" fill="var(--icon-color, currentColor)"></path></svg><span>Vis mer</span></button></div>
            ""","")
            article.html = article.html.replace("""
            <div class=" hyperion-css-1pnpwpe"><div class=" hyperion-css-c6o1b4" data-variants="[{&quot;sizes&quot;:[[1,1],[580,400],[580,500]],&quot;deviceType&quot;:&quot;desktop&quot;,&quot;minDisplayWidth&quot;:580,&quot;invCode&quot;:&quot;no-vg-{deviceType}-article_netboard_2&quot;,&quot;probableWidth&quot;:580,&quot;probableHeight&quot;:400,&quot;preloading&quot;:200,&quot;safeframeConfig&quot;:{&quot;allowExpansionByOverlay&quot;:false,&quot;allowExpansionByPush&quot;:false}},{&quot;sizes&quot;:[[1,1],[580,400],[580,500]],&quot;deviceType&quot;:&quot;tablet&quot;,&quot;minDisplayWidth&quot;:580,&quot;invCode&quot;:&quot;no-vg-{deviceType}-article_netboard_2&quot;,&quot;probableWidth&quot;:580,&quot;probableHeight&quot;:400,&quot;preloading&quot;:200,&quot;safeframeConfig&quot;:{&quot;allowExpansionByOverlay&quot;:false,&quot;allowExpansionByPush&quot;:false}},{&quot;sizes&quot;:[[1,1],[320,250],[320,400],[300,250],[336,280],[5,250],[5,400]],&quot;allowedFormats&quot;:[&quot;banner&quot;,&quot;native&quot;,&quot;outstream&quot;],&quot;deviceType&quot;:&quot;mobile&quot;,&quot;minDisplayWidth&quot;:300,&quot;invCode&quot;:&quot;no-vg-{deviceType}-article_board_2&quot;,&quot;probableWidth&quot;:320,&quot;probableHeight&quot;:250,&quot;preloading&quot;:200,&quot;safeframeConfig&quot;:{&quot;allowExpansionByOverlay&quot;:false,&quot;allowExpansionByPush&quot;:false}}]" data-refresh="false" data-show-label="true" data-ad-subtype="text-ad" data-device-type="desktop" data-is-last="false" data-theme="default" id="adPlacement_5"><div id="adPlacement_5-button" class="hyperion-css-19vk29s"></div></div></div>
            ""","")
            article.html = article.html.replace("""
            <div class="hyperion-css-j499fm"><h2 class="hyperion-css-11re7f5" data-test-tag="widget:title">Mer om</h2><div class="bundle hyperion-css-6nuwex"><ol class="hyperion-css-19mvxvm"><li class="hyperion-css-1og0r8"><a data-test-tag="internal-link" href="/tag/tv-serier-2" class="hyperion-css-1c5g4wr" rel="" target="" aria-label="TV-serier"><span class="hyperion-css-0">TV-serier</span></a></li><li class="hyperion-css-1og0r8"><a data-test-tag="internal-link" href="/tag/one-tree-hill" class="hyperion-css-1c5g4wr" rel="" target="" aria-label="One tree hill"><span class="hyperion-css-0">One tree hill</span></a></li></ol></div></div>
            ""","")
            return article.text

    def tv2(self, url):
        response = self.ses.get(url)
        if response.status_code == 200:
            html_content = response.html
            article = html_content.find('div.clearfix', first=True)
            return article.text

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
        "NRK Rogaland": scraper.nrk,
        'NRK Siste nytt': scraper.nrk,
        'vg.no': scraper.vg_no,
        'tv2.no': scraper.tv2,
        'aftenposten.no': scraper.no_auth,
        'nettavisen.no': scraper.no_auth,
    }

    print(method_name)

    func = methods.get(method_name)

    if func:
        return func(scraper.filter_article_body_source(article_body))  # Executing the chosen function
    else:
        raise ValueError(f"Invalid method name: {method_name}")  # Raising error for invalid source name
