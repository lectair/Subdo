import requests
import typer
import time
import sys
import re
from bs4 import BeautifulSoup as bs4
from crtsh import crtshAPI


def scraper_process(verbose, shodan_cookie, target):
    # - Shodan
    if verbose:
        typer.echo("> Start Shodan scraping for subdomains.")
        time.sleep(1)
    response = requests.get(f"https://www.shodan.io/domain/{target}", headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
        'Cookie': f'polito="{shodan_cookie}"'}).text
    data_shodan = bs4(response, 'html.parser')
    if verbose:
        if verbose == 3:
            with open('last_shodan_scrape.html', 'w', encoding='utf-8') as shodan_file:
                shodan_file.write(response)
            typer.echo("> START SHODAN HTML RESPONSE:")
        typer.echo(
            f"{bs4(response, 'html.parser').prettify()}\n\n> END SHODAN HTML RESPONSE\n> Finished Shodan scraping.") if verbose == 3 else typer.echo(
            "> Finished Shodan scraping.")
    try:
        shodan_subdomains = []
        parent = data_shodan.find("ul", {"id": "subdomains"}).find_all("li")
        for element in parent:
            shodan_subdomains.append(f"{element.text}.{target}")
    except IndexError:
        typer.echo("> Error scraping subdomains from Shodan.\nMaybe the target doesn't exist? Or you did not enter the cookie?\nTip: Switch verbosity to 2 to see the HTML response.\n")
        shodan_subdomains = []
    if verbose:
        typer.echo(f"> Found {len(shodan_subdomains)} subdomains in Shodan.")
        typer.echo(shodan_subdomains)
    # - Crt.sh
    if verbose:
        typer.echo("> Start crt.sh scraping for subdomains.")
        time.sleep(1)
    data = crtshAPI().search(target)
    if verbose:
        if verbose == 3:
            with open('last_crt_scrape.html', 'w', encoding='utf-8') as crt_file:
                crt_file.write(data)
            typer.echo("> START CRT.SH JSON RESPONSE:")
        typer.echo(
            f"{data}\n\n> END CRT.SH JSON RESPONSE\n> Finished Crt.sh scraping.") if verbose == 3 else typer.echo(
            "> Finished Crt.sh scraping.")
    try:
        crt_subdomains = []
        for i in data:
            a, b = i['common_name'], i['name_value']
            if "\n" in b:
                subdomains = b.split("\n")
                for subdomain in subdomains:
                    crt_subdomains.append(subdomain)
            else:
                crt_subdomains.append(b)
            crt_subdomains.append(a)

        crt_subdomains = list(set(crt_subdomains))
    except IndexError:
        typer.echo("> Error scraping subdomains from crt.sh. Aborted!\nMaybe the target doesn't exist?\n\nTip: Switch verbosity to 2 to see the HTML response.")
        sys.exit(1)
    if verbose:
        typer.echo(f"> Found {len(crt_subdomains)} subdomains in crt.sh.")
        typer.echo(crt_subdomains)
    # -- Finished scraping
    subdomains = sorted(list(filter(None, list(set(shodan_subdomains + crt_subdomains)))))
    for subdomain in subdomains:
        subdomains.remove(subdomain) if "*" in subdomain else ""
    return subdomains
