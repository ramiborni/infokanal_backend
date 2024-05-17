import re

import requests_html
from bs4 import BeautifulSoup
from langchain_community.document_transformers.beautiful_soup_transformer import BeautifulSoupTransformer
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from langchain.docstore.document import Document


class Scrapper:
    def __init__(self):
        # Initialize the HTML Session for the web scraper
        self.ses = requests_html.HTMLSession()

    def scrape_without_source(self, source_name: str, source_url: str):
        return self.scrape_with_bs4(source_url)

    def filter_article_body_source(self, source: str, url: str):
        return self.choose_scraping_method(source, url)

    def scrape_with_bs4(self, source_url: str, response=None):
        try:

            if response is None:
                response = self.ses.get(source_url)
                html = response.html.html
                doc = [Document(page_content=html)]  # Langchain needs Array of Document
                bs_transformer = BeautifulSoupTransformer()
                docs_transformed = bs_transformer.transform_documents(doc,
                                                                      tags_to_extract=["div", "span", "h1", "h2", "h3",
                                                                                       "h4", "h5", "article"])
                print(docs_transformed)
                result = str(docs_transformed[0].page_content)
                return result
            else:
                html = None
                if isinstance(response, requests_html.HTML):
                    html = response.html
                else:
                   html = response.html.html
                doc = [Document(page_content=html)]  # Langchain needs Array of Document
                bs_transformer = BeautifulSoupTransformer()
                docs_transformed = bs_transformer.transform_documents(doc,
                                                                      tags_to_extract=["div", "span", "h1", "h2", "h3",
                                                                                       "h4", "h5", "article"])
                print(docs_transformed)
                result = str(docs_transformed[0].page_content)
                return result
        except Exception as e:
            print(e)
            return None

    def karmoynytt(self, url):
        # Function to scrape data from karmoynytt.no
        # Cookies are used here for handling sessions (if needed)
        cookies = {
            'PHPSESSID': 'nnhc5747n940mgovcphivg7fv2',
            'REMEMBERME': 'Qm9kb1xVc2VyQnVuZGxlXEVudGl0eVxDdXN0b21lcjpaV2RwYkM1dFlYSjBhVzR1YzI5c1ltVnlaMEJuYldGcGJDNWpiMjA9OjE3ODQ2MTM1Mjg6NjM1OTY0MTNlYmVjNWRlNmM4ZGZjODEyZDQ0MzZjN2RlYzRiMzI3ZGFlMWJhYWQ1ZTMzYWViYWMzYjY1NmE1Mw%3D%3D',
        }
        response = self.ses.get(url, cookies=cookies)

        if response.status_code == 200:
            return self.scrape_with_bs4(url, response)
        else:
            print(response.status_code, response.text)
            return "Failed to fetch the page."

    def h_avis(self, url):
        try:
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

            for attempt in range(5):  # Two attempts: first one and then a refresh

                response = self.ses.get(url, cookies=cookies)

                if response.status_code == 200:
                    if response.html:
                        return self.scrape_with_bs4(source_url=url, response=response)
                    else:
                        # If the HTML is empty, refresh (make another request) and save cookies
                        print("HTML was empty, refreshing page.")
                        cookies = response.cookies
                else:
                    print(response.status_code, response.text)
                    return "Failed to fetch the page."
        except:
            return None

    def nrk(self, url):
        # Function to scrape data from nrk.no
        response = self.ses.get(url)
        if response.status_code == 200:
            return self.scrape_with_bs4(source_url=url, response=response)

    def vg_no(self, url):
        # Function to scrape from vg.no
        response = self.ses.get(url)
        if response.status_code == 200:
            return self.scrape_with_bs4(source_url=url, response=response)

    def tv2(self, url):
        response = self.ses.get(url)
        if response.status_code == 200:
            return self.scrape_with_bs4(source_url=url, response=response)

    def dagbladet(self, url):
        try:
            response = self.ses.get(url)
            if response.status_code == 200:
                return self.scrape_with_bs4(source_url=url, response=response)
        except:
            return None

    def sunnhordland(self, url):
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        driver = webdriver.Firefox(options=firefox_options)
        cookie_list = [
            {
                "name": "abx.v2",
                "value": "A",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1698872447.471362,
                "httpOnly": False,
                "secure": True
            },
            {
                "name": "abx.v1",
                "value": "40",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1698872447.47131,
                "httpOnly": False,
                "secure": True
            },
            {
                "name": "_pctx",
                "value": "%7Bu%7DN4IgrgzgpgThIC4B2YA2qA05owMoBcBDfSREQpAeyRCwgEt8oBJAEzIE4AmHrjgRg4A2ABwB2fgFYxABjEcOAZhABfIA",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1725284506,
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            },
            {
                "name": "_pcid",
                "value": "%7B%22browserId%22%3A%22lkvmsk6751wyqyi2%22%7D",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1725284506,
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            },
            {
                "name": "cX_P",
                "value": "lkvmsk6751wyqyi2",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1725284506,
                "httpOnly": False,
                "secure": True
            },
            {
                "name": "cX_G",
                "value": "cx%3Aqlyhzj472dcb2sc4cdofy1gg9%3A36i71elx1mkt9",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1725223831,
                "httpOnly": False,
                "secure": True
            },
            {
                "name": "id-jwt",
                "value": "eyJraWQiOiIzYWNkODdmNS0zYmQyLTQ5ZTMtYWFhOC0wYTI5ZjU2MzY1YTIiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJzZHJuOnNwaWQubm86Y2xpZW50OjYzMDg2ZGY5MmU2NzVhNjQ5YTE5NDk5MiIsInN1YiI6Ijg4MjQ1NmMwLTkwMTUtNWQ3OS05MGI0LTVlYzY0YjI0ZDY0YyIsInVzZXJfaWQiOiI1NDczMjAiLCJpc3MiOiJodHRwczpcL1wvc2Vzc2lvbi1zZXJ2aWNlLmxvZ2luLnNjaGlic3RlZC5jb20iLCJleHAiOjE3MjI2MzI3MTksImlhdCI6MTY5MTA5NjcxOSwianRpIjoiOTk5ODhhNjEtYWY3My00MzI0LTkxNTQtMDU1ZGZkMDU1YjliIn0.o5U5xoo1HV7QB90E7Ari8HM39gxLhF28AlxcpOmBtv14vL5SVfcBUBnIilNYedU82inahfSZvAoC68C945CFoYhafLq1fkwEGWvKhP7IQmVieNFDcwelTTkfwFblvbYSoDag3OGyNdRaEH7zGgaRYteJWS1TOeOQ8AbVGToaqq3kSF4ms-7x3fZ57l94D8Ng1jKscleVoVX55Vel7g73s0CiaIa4oJIAMigCkb3YescxUKyJyTch5kBuxVHwzaDlNH9wuplRdfWwVcxtUMTI8J1VH1Rddq_uksaMuhGyhamHSHdYooQmAMcnHFh51eSdJFxBiYvboXPCoDPvVWMwcVJN3B-WLZoolLMfhxRunnGMZY6BiRklkpNScG3RD32bXP2_ZgbqJ32GCF44yB3B5ThM8aDsjuM7njhWD_NIaFO-CZWLlv0QmwhBUo-F2NuTs3dk5q-_-L7iSrEr_vWW9e0dkZpS4emsXvni2mYtRKAOyATgfaMyRGgvapoRcTPLpVjyR9TOv3ipT8EzHz5hh4yPCC1D173yGKmT3k58OBaWB0THp8wYhWibfoYxDFKJmqOqfUV5h1jutYUyAD_vFQl9Z7FttH3qaspNRmIsO4cErFU2tlfLpw3NrFHWranS9xRaig_5hojW-gd1W7OgiFTuFVu-oCKY7uQ0Zm4kKSg",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1722632718.288673,
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax"
            },
            {
                "name": "SP_ID",
                "value": "eyJjbGllbnRfaWQiOiI2MzA4NmRmOTJlNjc1YTY0OWExOTQ5OTIiLCJhdXRoIjoiVHdYMUo5WlhXTUFHV1RIdFNOR2RXc1hFdG9XQjFKYllIamJ3SXFRSkZjNzlQcURWYnhqUlBiby1WVXFhblVFWFNxeHVhYk1JODUwX0lvUk4yN3U4X0t4bjJjbjQ5Z1RLQ1otQVFoRzR5WU0ifQ",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1722692502,
                "httpOnly": False,
                "secure": False
            },
            {
                "name": "pws.v2",
                "value": "dHVwbGVzPSgoU1VOLDE2OTExNTY3OTEpKSxpZC1qd3Q9ZXlKcmFXUWlPaUl6WVdOa09EZG1OUzB6WW1ReUxUUTVaVE10WVdGaE9DMHdZVEk1WmpVMk16WTFZVElpTENKaGJHY2lPaUpTVXpJMU5pSjkuZXlKaGRXUWlPaUp6WkhKdU9uTndhV1F1Ym04NlkyeHBaVzUwT2pZek1EZzJaR1k1TW1VMk56VmhOalE1WVRFNU5EazVNaUlzSW5OMVlpSTZJamc0TWpRMU5tTXdMVGt3TVRVdE5XUTNPUzA1TUdJMExUVmxZelkwWWpJMFpEWTBZeUlzSW5WelpYSmZhV1FpT2lJMU5EY3pNakFpTENKcGMzTWlPaUpvZEhSd2N6cGNMMXd2YzJWemMybHZiaTF6WlhKMmFXTmxMbXh2WjJsdUxuTmphR2xpYzNSbFpDNWpiMjBpTENKbGVIQWlPakUzTWpJMk16STNNVGtzSW1saGRDSTZNVFk1TVRBNU5qY3hPU3dpYW5ScElqb2lPVGs1T0RoaE5qRXRZV1kzTXkwME16STBMVGt4TlRRdE1EVTFaR1prTURVMVlqbGlJbjAubzVVNXhvbzFIVjdRQjkwRTdBcmk4SE0zOWd4TGhGMjhBbHhjcE9tQnR2MTR2TDVTVmZjQlVCbklpbE5ZZWRVODJpbmFoZlNadkFvQzY4Qzk0NUNGb1loYWZMcTFma3dFR1d2S2hQN0lRbVZpZU5GRGN3ZWxUVGtmd0ZibHZiWVNvRGFnM09HeU5kUmFFSDd6R2dhUll0ZUpXUzFUT2VPUThBYlZHVG9hcXEza1NGNG1zLTd4M2ZaNTdsOTREOE5nMWpLc2NsZVZvVlg1NVZlbDdnNzNzMENpYUlhNG9KSUFNaWdDa2IzWWVzY3hVS3lKeVRjaDVrQnV4Vkh3emFEbE5IOXd1cGxSZGZXd1ZjeHRVTVRJOEoxVkgxUmRkcV91a3NhTXVoR3loYW1IU0hkWW9vUW1BTWNuSEZoNTFlU2RKRnhCaVl2Ym9YUENvRFB2VldNd2NWSk4zQi1XTFpvb2xMTWZoeFJ1bm5HTVpZNkJpUmtsa3BOU2NHM1JEMzJiWFAyX1pnYnFKMzJHQ0Y0NHlCM0I1VGhNOGFEc2p1TTduamhXRF9OSWFGTy1DWldMbHYwUW13aEJVby1GMk51VHMzZGs1cS1fLUw3aVNyRXJfdldXOWUwZGtacFM0ZW1zWHZuaTJtWXRSS0FPeUFUZ2ZhTXlSR2d2YXBvUmNUUExwVmp5UjlUT3YzaXBUOEV6SHo1aGg0eVBDQzFEMTczeUdLbVQzazU4T0JhV0IwVEhwOHdZaFdpYmZvWXhERktKbXFPcWZVVjVoMWp1dFlVeUFEX3ZGUWw5WjdGdHRIM3Fhc3BOUm1Jc080Y0VyRlUydGxmTHB3M05yRkhXcmFuUzl4UmFpZ181aG9qVy1nZDFXN09naUZUdUZWdS1vQ0tZN3VRMFptNGtLU2csc2lnPTB4MDQ5ZjllODg2ZGY1Yzg1YTgwNjZjMWQ5NmYzZjJjOGI2NWQ4Yjc0MzRiNDFhMmI2MDA2YjlmNDNhYTVmNDdkNQ==",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1722696971.962292,
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            },
            {
                "name": "_k5a",
                "value": "61@{\"u\":[{\"uid\":\"bFBC2l3LjVvHqm4L\",\"ts\":1691156505},1691246505]}",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1722778905,
                "httpOnly": False,
                "secure": False,
                "sameSite": "Strict"
            },
            {
                "name": "__mbl",
                "value": "61@{\"u\":[{\"uid\":\"9XhDCZT0XLpsNHpK\",\"ts\":1691156506},1691246506]}",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1722778906,
                "httpOnly": False,
                "secure": False,
                "sameSite": "Strict"
            },
            {
                "name": "_pulsesession",
                "value": "%5B%22sdrn%3Aschibsted%3Asession%3Af8725cad-7dd4-4fb3-a674-bed516d9bebb%22%2C1691164442662%2C1691164442662%5D",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1691166242,
                "httpOnly": False,
                "secure": True
            },
            {
                "name": "_pulse2data",
                "value": "d2638605-c851-4ce1-aad6-c113acde631c%2Cv%2C547320%2C1691165343709%2CeyJpc3N1ZWRBdCI6IjIwMjMtMDgtMDNUMjE6MDU6MjlaIiwiZW5jIjoiQTEyOENCQy1IUzI1NiIsInJlSXNzdWVkQXQiOiIyMDIzLTA4LTA0VDE1OjU0OjAzWiIsImFsZyI6ImRpciIsImtpZCI6IjIifQ..5GfpOAeGIIgutcRd_N4XAg.GSiEHMpi_rv5WlyPG0c6IAxVVP3nO3JxzCG1wFAYiwMIvb61iLlaLIBCBJrp6ufGu9YcTHOUR5ooKD3lgJnmBoLLzy7YjM-4DEfXI7z0nfkDad0EU8A8C1ctfDslKKcdNn4eag6PmaTVpL-8c2B5XptfBUuti2Hg4Vpb5Q4Ts9rKvqYWu_FWy1zYP3Bbfm32CwSjoYfC5DDWIk4daHGDWTU9D3hXM6EHIUIbEZZh1gRsHaHqLq0bM5P3nj5L5RXcfnHSp6AlxOjquaJuRyguvnFbMN2DAxN5yNCNelgU4ymlU7MFok6c1IHMBA6E8zVGzv-V_ut14Q9p_tFa3vVIZhz8Fud0iaaVDO98vKPEuT5Dcg7Od9P7orE8yYQFHr_8C0-Fiz6GdsxRWR6HO6sAQSD7O3Ope1mnbrLHSWD_BQ2flhXqkYijvGpgsdajnXgho-tLgPD9-O8E-AiIl7WjVYYdz0O4F6aDb8YjDtM642Q.VDnwXyCBFmgU9pMf_XHRzA%2C%2C0%2CTrue%2C%2CeyJraWQiOiIyIiwiYWxnIjoiSFMyNTYifQ..RwOXgF-I4qS-idErlVNKojL5azoFMRIjhFtxiA-MsrI",
                "domain": ".sunnhordland.no",
                "path": "/",
                "expires": 1725724443.709747,
                "httpOnly": False,
                "secure": True
            }
        ]
        driver.get(url)
        for cookie in cookie_list:
            driver.add_cookie(cookie)
        # Set the required sessionStorage item
        driver.execute_script('sessionStorage.setItem("_cX_S", "lkwmx3x7cwhvl81f");')
        driver.get(url)
        # Extract the HTML content
        html_content = driver.page_source
        driver.quit()

        # Pass the HTML content to requests_html
        rs = requests_html.HTML(html=html_content)
        return self.scrape_with_bs4(source_url=url, response=rs)

    def grannar(self, url: str):
        cookie_list = [
            {
                "name": "_gid",
                "value": "GA1.2.575921173.1691014390",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1691245684,
                "httpOnly": False,
                "secure": False
            },
            {
                "name": "euconsent-v2",
                "value": "CPv7UwAPv7UwAAKAvANODLCsAP_AAH_AABpwJhNX_H__bW9r8f7_aft0eY1P9_j77uQxBhfJk-4F3LvW-JwX52E7NF36tqoKmR4Eu3LBIUNlHNHUTVmwaokVryHsak2cpTNKJ6BEkHMRO2dYCF5vmxtjeQKY5_p_d3fx2D-t_dv-39z3z81Xn3dZf-_0-PCdU5-9Dfn9fRfb-9IP9_78v8v8_9_rk2_eT13_79_7_H9-f_87_QTBAJMNS4gC7MocCbQMIoUQIwrCAigUAABAMDRAQAODAp0RgE-sIkAKEUARgRAhwBRkQCAAASAJCIAJAiwQAAACAQAAgAQCIQAMDAIKACwEAgABAdAxRCgAECQgSIiIhTAgKgSCAlsqEEoLpDTCAKssAKARGwUACIJARWAAICwcAwRICViwQJcQbRAAMACAUSoVqKT00BCgmbLAAAAA.YAAAAAAAAAAA",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1724792749.401281,
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            },
            {
                "name": "addtl_consent",
                "value": "1~43.3.9.6.9.13.6.4.15.9.5.2.11.1.7.1.3.2.10.33.4.6.9.17.2.9.20.7.20.5.20.6.5.1.4.11.29.4.14.9.3.10.6.2.9.6.6.9.8.29.4.5.3.1.6.21.1.17.10.9.1.8.6.2.8.3.4.146.65.1.17.1.18.25.35.5.18.9.7.41.2.4.18.24.4.9.6.5.2.14.18.7.3.2.2.8.28.8.6.3.10.4.20.2.13.4.10.11.1.3.22.16.2.6.8.6.11.6.5.33.11.8.1.10.28.12.1.5.19.9.6.40.17.4.9.15.8.7.3.12.7.2.4.1.7.12.13.22.13.2.14.10.1.4.15.2.4.9.4.5.4.7.13.5.15.4.13.4.14.10.15.2.5.6.2.2.1.2.14.7.4.8.2.9.10.18.12.13.2.18.1.1.3.1.1.9.25.4.1.19.8.4.8.5.4.8.4.4.2.14.2.13.4.2.6.9.6.3.2.2.3.5.2.3.6.10.11.6.3.19.11.3.1.2.3.9.19.26.3.10.7.6.4.3.4.6.3.3.3.3.1.1.1.6.11.3.1.1.11.6.1.10.5.8.3.2.2.4.3.2.2.7.15.7.14.1.3.3.4.5.4.3.2.2.5.5.1.2.9.7.9.1.5.3.7.10.11.1.3.1.1.2.1.3.2.6.1.12.8.1.3.1.1.2.2.7.7.1.4.3.6.1.2.1.4.1.1.4.1.1.2.1.8.1.7.4.3.3.3.5.3.15.1.15.10.28.1.2.2.12.3.4.1.6.3.4.7.1.3.1.4.1.5.3.1.3.4.1.5.2.3.1.2.2.6.2.1.2.2.2.4.1.1.1.2.2.1.1.1.1.2.1.1.1.2.2.1.1.2.1.2.1.7.1.4.1.2.1.1.1.1.2.1.4.2.1.1.9.1.6.2.1.6.2.3.2.1.1.1.2.5.2.4.1.1.2.2.1.1.7.1.2.2.1.2.1.2.3.1.1.2.4.1.1.1.5.1.3.6.3.1.5.5.4.1.2.3.1.4.3.2.2.3.1.1.1.1.1.11.1.3.1.1.2.2.5.2.3.3.5.2.7.1.1.2.5.1.9.5.1.3.1.8.4.5.1.9.1.1.1.2.1.1.1.4.2.13.1.1.3.1.2.2.3.1.2.1.1.1.2.1.3.1.1.1.1.2.4.1.5.1.2.4.3.8.2.2.9.7.2.2.1.2.1.3.1.6.1.7.1.1.2.6.3.1.2.1.200.200.100.100.200.400.100.100.100.200.200.1700.100.204.596.100.1000.800.500",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1724792749.402254,
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            },
            {
                "name": "__qca",
                "value": "P0-1780127653-1691096742235",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1724965549,
                "httpOnly": False,
                "secure": False
            },
            {
                "name": "aboid_token",
                "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjkwNSwiY2xpZW50SWQiOjQsImlhdCI6MTY5MTA5NjgxNywiZXhwIjoxNzIyNjU0NDE3LCJhdWQiOiJhYm9JZENsaWVudDphY2Nlc3MiLCJpc3MiOiJodHRwczovL2FwaS5hYm9pZC5ubyIsInN1YiI6IjkwNSIsImp0aSI6ImNjZjU2ZGNkLWYzNWMtNDgzMy05YTBiLTZlMTE4Zjg2YTFmYyJ9.z7zaA9umRIvte_g4a5XaSVy74Z9oqZTQIoaMnq5lKxs",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1722632817.438722,
                "httpOnly": False,
                "secure": False
            },
            {
                "name": "aboid_userid",
                "value": "905",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1722632817.43879,
                "httpOnly": False,
                "secure": False
            },
            {
                "name": "auth-token",
                "value": "RDI2dVd1WlV5bTBPa3ZNcHliVlNYMXFWWWxxbHhPaVhNVWFOOGsyYTNjUlJNVktZdjJwRWJaTnBaWWdYM2NsZUp0RnRJa3duZXVtTXVnU2FPTUpaRkdOYzdqYWlGM2FoY0thcXdiMWtYZUtEdm1SNGN5Q0NiT2Z2MnlNT2J3SGtlRWtnRkNseWQzMjV4VmtUWGZKSkxuZ0syYzFUR093WFp5UFNsQmFEZWFDbnk2T1o5dEpQV0FBRlVmNTFPLzBIa01IdTBRNXdIMFZhcDZyVW16WjJQZnZlR1VUNnV2N1lRbG9IeGEzMjB5UmdIdVBwVmRMYnRqMDNlSHl1OGRXbEdTMklQalZGWU5OMGhyM2lpYURRQTAxZzg0WWpBQWN1NC9LblpFYWNWZ1gxbkl1MEdXUUNkby8rNGUvU1Z3a1JPRmFjaEQ5aWpLSThzb2tFbVdFL0Y3dEtoNHpsbGw2Mkt1bFdiUmNCclNtcitNOFl0MTUzRUZxdFg0c1JhRS9ac0UzcWtabVJrS00wY3pnSzVDcjZJMTJrd2NobmNrdUJ5Zkd5UVZEK0g3andQbHk4WmJtQWhIci9rN1lnUDZJZGMzYkdQWEpvS2hPaHhmSll3Z014MmtMOWtCT24relhjSmVBeVJzSlEzWk09",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1722632817.438806,
                "httpOnly": False,
                "secure": False
            },
            {
                "name": "ap-cookie-last-checked",
                "value": "1691096817",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1722632817.438824,
                "httpOnly": False,
                "secure": False
            },
            {
                "name": "_ga_MMXH4E6N0V",
                "value": "GS1.1.1691159285.5.0.1691159285.0.0.0",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1725719285.060377,
                "httpOnly": False,
                "secure": False
            },
            {
                "name": "_ga",
                "value": "GA1.1.1574498605.1691014390",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1725719285.061631,
                "httpOnly": False,
                "secure": False
            },
            {
                "name": "_ga_CT9DF7D30N",
                "value": "GS1.2.1691159295.4.0.1691159295.0.0.0",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1725719295.310464,
                "httpOnly": False,
                "secure": False
            },
            {
                "name": "_ga_9P2QJ3KM9E",
                "value": "GS1.2.1691159295.5.0.1691159295.0.0.0",
                "domain": ".grannar.no",
                "path": "/",
                "expires": 1725719295.385847,
                "httpOnly": False,
                "secure": False
            }
        ]
        cookies = {cookie['name']: cookie['value'] for cookie in cookie_list}
        response = self.ses.get(url, cookies=cookies)

        if response.status_code == 200:
            return self.scrape_with_bs4(source_url=url, response=response)

    def standard_scrapper(self, url: str):
        return self.scrape_with_bs4(source_url=url)

    def choose_scraping_method(self, source_name: str, url: str):
        try:

            if source_name == 'karmoynytt.no':
                return self.karmoynytt(url)
            elif source_name == 'h-avis.no':
                return self.h_avis(url)
            elif source_name == 'grannar.no':
                return self.grannar(url)
            elif source_name == 'sunnhordland.no':
                return self.sunnhordland(url)
            elif source_name == 'NRK Rogaland' or source_name == 'NRK Siste nytt':
                return self.nrk(url)
            elif source_name == 'vg.no':
                return self.vg_no(url)
            elif source_name == 'tv2.no':
                return self.tv2(url)
            elif source_name == 'dagbladet.no':
                return self.dagbladet(url)
            else:
                return self.standard_scrapper(url)
        except Exception as e:
            print(f"Error processing request: {e}")
            return None
