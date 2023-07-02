#The Collector - A little tool to maybe help you find some proxy servers and verify they work
# BuryNice 2023
import re
import requests
import time
import argparse
import webbrowser

ip_regex = r'\b(?:\d{1,3}\.){3}\d{1,3}\b:\d+'
port_regex = r':\d{1,5}'

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
}

def get_ips_from_search_engines(query, num_pages):
    ips = set()
    search_engines = [
        'https://www.bing.com/search?q={query}&first={page}',
        'https://www.google.com/search?q={query}&start={page}&num=10&ie=UTF-8',
        'https://search.yahoo.com/search?p={query}&b={page}',
        'https://duckduckgo.com/html/?q={query}&s={page}&kl=us-en'
    ]

    for search_engine in search_engines:
        zero_result_count = 0
        for page in range(num_pages):
            url = search_engine.format(query=query, page=page*10)

            try:
                res = requests.get(url, headers=headers)
                res.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if res.status_code == 400:
                    print(f'{search_engine} - Page {page+1}: Bad request error: {e}')
                elif res.status_code == 404:
                    print(f'{search_engine} - Page {page+1}: Page not found error: {e}')
                elif res.status_code == 429:
                    print(f'{search_engine} - Page {page+1}: Too many requests error: {e}')
                    try:
                        res = requests.get(url, headers=headers)
                        res.raise_for_status()
                        matches = re.findall(ip_regex, res.text)
                        # ...
                    except requests.exceptions.HTTPError as err:
                        if err.response.status_code == 439:
                            print(f'Captcha detected for URL: {url}')
                            webbrowser.open(url)
                            continue
                        else:
                            # Handle other HTTP errors
                            print(f'Error {err.response.status_code} occurred for URL: {url}')
                            continue
                    except Exception as e:
                        # Handle other exceptions
                        print(f'Error occurred for URL: {url}: {str(e)}')
                        continue
                else:
                    print(f'{search_engine} - Page {page+1}: HTTP error: {e}')
                break

            matches = re.findall(ip_regex, res.text)
            if not matches:
                zero_result_count += 1
                if zero_result_count > 2:
                    print(f'{search_engine} - Page {page+1}: No results found 3 times in a row, moving on')
                    break
            else:
                zero_result_count = 0
                ips.update(matches)
                print(f'{search_engine} - Page {page+1}: Found {len(matches)} IPs')
            time.sleep(2)

    return list(ips)


COMMON_PORTS = [80, 1080, 3128, 8080, 8888, 9050, 4480, 6588, 8088, 9000, 9999]

def test_ports(ip_list, proxy=None):
    working_proxies = []
    checked = set()
    for i, ip in enumerate(ip_list):
        print(f'Testing {ip} ({i+1}/{len(ip_list)})')
        for port in COMMON_PORTS:
            if (ip, port) in checked:
                continue
            try:
                if proxy:
                    proxies = {
                        'http': f'http://{proxy}',
                        'https': f'https://{proxy}'
                    }
                    proxy_url = f'http://{ip}:{port}'
                    res = requests.get('https://www.google.com', proxies=proxies, timeout=0.5)
                else:
                    proxy_url = f'http://{ip}:{port}'
                    res = requests.get('https://www.google.com', timeout=0.5)
                    
                if res.status_code == 200:
                    working_proxies.append(proxy_url)
                    print(f'{proxy_url} is working')
                else:
                    print(f'{proxy_url} returned status code {res.status_code}')
                    
                checked.add((ip, port))
            except requests.exceptions.RequestException as e:
                print(f'{proxy_url} raised an exception: {e}')
            except Exception as e:
                print(f'An error occurred while testing {proxy_url}: {e}')

    return working_proxies


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='The Collector - a Proxy Ripper built by BuryNice')
    parser.add_argument('query', type=str, help='Query to search for')
    parser.add_argument('-p', '--pages', type=int, default=1, help='Number of pages to search')
    parser.add_argument('-t', '--time', type=int, default=0, help='Maximum time in seconds to spend searching')
    parser.add_argument('--proxy', type=str, default=None, help='Proxy server to use')
    args = parser.parse_args()

    start_time = time.time()

    ip_list = get_ips_from_search_engines(args.query, args.pages)
    working_proxies = test_ports(ip_list, args.proxy)

    with open('output.txt', 'w') as f:
        for proxy in working_proxies:
            f.write(proxy + '\n')
            print(f'{proxy} added to output file')

    if not working_proxies:
        print('No working proxies found. Output file may be empty.')

    end_time = time.time()
   
