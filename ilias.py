import urllib.request
from bs4 import BeautifulSoup


class IliasClient:
    def __init__(self, cookie):
        self.base_url = "https://www.ilias.uni-koeln.de/ilias"

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
            "Accept-Encoding": "none",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
            "authority": "www.ilias.uni-koeln.de",
            "method": "GET",
            "path": "/ilias/ilias.php?ref_id=4420106&cmdClass=xocteventgui&cmdNode=pf:p7:18a&baseClass=ilObjPluginDispatchGUI",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "en-US,en;q=0.9,de;q=0.8",
            "cache-control": "max-age=0",
            "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"    "sec-ch-ua-mobile": "?0"',
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "cross-site",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
        }
        headers["cookie"] = cookie
        self.headers = headers

    # -------------- get page that has links to all lectures --------------
    def get_video_overview_url(self, url):
        req = urllib.request.Request(
            # f"{base_url}/ilias.php?ref_id=4420106&cmdClass=xocteventgui&cmdNode=pf:p7:18a&baseClass=ilObjPluginDispatchGUI",
            url,
            headers=self.headers,
        )

        with urllib.request.urlopen(req) as url:
            video_overview_raw = url.read().decode("utf-8")

        soup = BeautifulSoup(video_overview_raw, "html.parser")
        script_tags = soup.find_all("script")

        search_string = "url: 'ilias.php?ref_id"

        def filter_by_content(tag):
            return tag.string and search_string in tag.string

        script_tag = list(filter(filter_by_content, script_tags))[0]
        matched_line = [
            line for line in script_tag.string.split("\n") if search_string in line
        ][0]
        url = matched_line.split("'")[1]

        return f"{self.base_url}/{url}"

    # -------------- get links to all lectures --------------
    def get_videos_data(self, url):
        req = urllib.request.Request(
            # f"{base_url}/{url}",
            url,
            headers=self.headers,
        )

        with urllib.request.urlopen(req) as url:
            video_links_raw = url.read().decode("utf-8")

        soup = BeautifulSoup(video_links_raw, "html.parser")

        tr1s = soup.find_all("tr", {"class": "tblrow1"})
        tr2s = soup.find_all("tr", {"class": "tblrow2"})

        trs = tr1s + tr2s

        def get_information_from_tr(tr):
            tds = tr.find_all("td")
            return {
                "title": tds[2].text,
                "datetime": tds[6].text,
                "instructor": tds[7].text,
                "link": tds[1].find("a")["href"],
            }

        trs = list(map(get_information_from_tr, trs))
        return trs

    # -------------- get stream link from lecture site --------------
    def get_stream_link(self, url):
        req = urllib.request.Request(
            f"https://www.ilias.uni-koeln.de/ilias/{url}",
            headers=self.headers,
        )

        with urllib.request.urlopen(req) as url:
            video_html_raw = url.read().decode("utf-8")

        soup = BeautifulSoup(video_html_raw, "html.parser")

        script_tag = soup.find_all("script")[-1]

        escaped_url = script_tag.string.split('"hls":[{"src":"')[1].split('"')[0]
        url = escaped_url.replace("\\", "")

        return url


if __name__ == "__main__":
    iliasClient = IliasClient(
        "ilClientId=uk; PHPSESSID=8f615198091ec708b341c3e8ef56ba0f; foundFirstPageLogin_8f615198091ec708b341c3e8ef56ba0f=1; skin=dark"
    )
    video_overview_url = iliasClient.get_video_overview_url(
        f"https://www.ilias.uni-koeln.de/ilias/ilias.php?ref_id=4420106&cmd=index&cmdClass=xocteventgui&cmdNode=pf:p7:18a&baseClass=ilObjPluginDispatchGUI"
    )
    video_links = iliasClient.get_video_data(video_overview_url)
    stream_link = iliasClient.get_stream_link(video_links[0]["link"])
