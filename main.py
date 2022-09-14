import datetime
import os
import sys
import requests
import time
import urllib.parse
import typer
#import threading
from os.path import exists as file_exists
from typing import Optional
from rich.console import Console
from rich.table import Table
from tqdm import tqdm

# Local imports
from open_tabs import tab_opener
from web_checker import check_reachable, check_intitle, check_inhtml, check_inurl
from scraper import scraper_process
from file_saver import save_file

requests.packages.urllib3.disable_warnings()
app = typer.Typer(add_completion=False)
console = Console()


# IMPORT REMOVED - WEB CHECKERS

# IMPORT REMOVED - BATCH OPENER


@app.command()
def main(target: str = typer.Option(None, help="Target URL."),
         browser: str = typer.Option("chrome", help="The browser to use for opening subdomains in tabs. Options: chrome, opera, edge, ie, epic, custom"),
         browser_executable: Optional[str] = typer.Option(None, help="Provide a custom browser executable if needed."),
         shodan_cookie: Optional[str] = typer.Option(None, help="The cookie to use for the Shodan scraping. Sometimes not needed."),
         path_suffix: Optional[str] = typer.Option("", help="The URL path suffix to use.\nExample: /robots.txt -> (google.com/robots.txt)"),
         subdomain_suffix: Optional[str] = typer.Option("", help="The subdomain suffix to use.\nExample: .test -> (subdomain.test.google.com)"),
         check_reachability: bool = typer.Option(False, help="Check if the hosts are reachable. If so, only save and open the reachable ones. If output_format isn't 'txt' the output will save both but will have a column for reachability. WARNING: This will connect to the target and will leak your actual IP."),
         open_tabs: bool = typer.Option(False, help="Open the subdomains in browser tabs."),
         save_output: bool = typer.Option(False, help="Whether or not to save the subdomain list. If selected, the output will be saved to a file within the Results folder."),
         output_format: str = typer.Option("txt", help="The format to save the output. Options: txt, csv, json."),
         output_dir: str = typer.Option(os.getcwd(), help="The directory to save the output."),
         batch_size: int = typer.Option(0, help="Open tabs in batch. Set this number to how many tabs you want to open at once."),
         custom_subdomains: str = typer.Option(None, help="Provide a file containing subdomains."),
         intitle: str = typer.Option(None, help=""),
         inhtml: str = typer.Option(None, help=""),
         inurl: str = typer.Option(None, help=""),
         favicon: str = typer.Option(None, help=""),
         timeout: int = typer.Option(5, help=""),
         #threads: int = typer.Option(1, help=""),
         verbose: int = typer.Option(0, help="The verbosity level.")
         ):
    """
        This script will take a target domain and will scrape its subdomains from
        Shodan & crt.sh. You can choose to check the reachable ones. Then the results
        will be saved to a file and opened in browser tabs if needed. You can also
        add a path/subdomain suffix, with wordlists or manually to try and find more
        subdomains bruteforcing the target.
    """
    # 1º Stage: Setting initial values for variables, printing banner & parameters if verbose and first time opening browser if needed.
    browser_executables = {
        "chrome": 'C:\\Program Files\\Google\\Chrome\\Application\\chrome',
        "opera": f'C:\\Users\\{os.getlogin()}\\AppData\\Local\\Programs\\Opera GX\\opera',
        "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge",
        "ie": "C:\\Program Files\\Internet Explorer\\iexplore",
        "epic": f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Epic Privacy Browser\\Application\\epic",
        "custom": f"{browser_executable}"
    }
    if output_format not in ["txt", "csv", "json"]:
        typer.echo(f"{output_format} is not a valid output format. Please choose from: txt, csv, json.")
        sys.exit(1)
    if subdomain_suffix:
        subdomain_suffix = subdomain_suffix.replace(".", "")
    if path_suffix:
        path_suffix = path_suffix.replace("/", "")
    if browser_executable:
        browser = "custom"
    if target:
        if ("http://" in target) or ("https://" in target):
            target = target.split("://")[1]
    if file_exists('shodan-cookie.txt') and not shodan_cookie:
        shodan_cookie = open('shodan-cookie.txt', 'r', encoding='utf-8').read().rstrip()
    if not target and not custom_subdomains:
        typer.echo(f"You must provide a target domain or a file containing subdomains.\n")
        sys.exit(1)
    elif custom_subdomains:
        try:
            with open(custom_subdomains, 'r', encoding='utf-8') as f:
                subdomains = f.readlines()
                if subdomains[0].count('.') >= 1:
                    subdomains = [subdomain.rstrip() for subdomain in subdomains]
                else:
                    if not target:
                        typer.echo(f"\nIf you don't provide a target when using custom subdomains and it can't be inferred from subdomains, the script can't work!\n")
                        sys.exit(1)
                    else:
                        subdomains = [subdomain.rstrip()+"."+target for subdomain in subdomains]
                if not subdomains:
                    typer.echo(f"The file {custom_subdomains} is empty.\n")
                    sys.exit(1)
            subdomains = sorted(list(filter(None, list(set(subdomains)))))
        except FileNotFoundError:
            typer.echo(f"The file {custom_subdomains} doesn't exist.\n")
            sys.exit(1)

    browser_executable = browser_executables[browser]
    if target:
        target = urllib.parse.urlparse("http://" + target).netloc
    # - Banner
    typer.echo('''
    ▄██████████  ███     █▄   ▀██████████▄    ▀█████████▄    ▄████████▄  
   ███     ████  ███     ███     ███     ███   ███    ▀███  ███      ███ 
   ███      █▀   ███     ███     ███     ███   ███     ███  ███      ███ 
   ███           ███     ███    ▄███▄▄▄▄███▀   ███     ███  ███      ███ 
 ▀█████████████  ███     ███   ▀▀███▀▀▀▀██▄    ███     ███  ███      ███ 
           ████  ███     ███     ███     ██▄   ███     ███  ███      ███ 
    ▄█     ████  ███     ███     ███     ███   ███    ▄███  ███      ███ 
  ▄██████████▀   ██████████▀    ▄██████████▀   ██████████▀   ▀████████▀  
                                                           
''')
    time.sleep(2)
    typer.echo(f"> Started at {str(datetime.datetime.now())[:-7]}.")
    if verbose:
        table = Table(header_style="white on black")
        table.add_column("Parameter", width=20, justify="left", style="white on black")
        table.add_column("Value", width=70, justify="left", style="black on white")
        table.add_row("Target", target)
        table.add_row("Browser", browser)
        table.add_row("Browser Executable", browser_executable)
        table.add_row("Shodan Cookie", shodan_cookie)
        table.add_row("Path Suffix", "/"+path_suffix)
        table.add_row("Subdomain Suffix", "."+subdomain_suffix)
        table.add_row("Check Reachability", str(check_reachability))
        table.add_row("Open Tabs", str(open_tabs))
        table.add_row("Save Output", str(save_output))
        table.add_row("Output Format", output_format)
        table.add_row("Output Directory", output_dir)
        table.add_row("Batch Size", str(batch_size))
        table.add_row("Custom Subdomains", custom_subdomains)
        table.add_row("In Title", intitle)
        table.add_row("In HTML", inhtml)
        table.add_row("In URL", inurl)
        table.add_row("Timeout", str(timeout))
        #table.add_row("Threads", str(threads))
        table.add_row("Verbosity Level", str(verbose))
        console.print(table)
        time.sleep(1)
    if not custom_subdomains:
        # 2º Stage: Scraping subdomains and manipulating them
        # IMPORT REMOVED - SCRAPER
        subdomains = scraper_process(verbose, shodan_cookie, target)
    if verbose:
        typer.echo(f"> Found {len(subdomains)} unique subdomains in total.")
        typer.echo(subdomains)
        print()
    if check_reachability:
        subdomains_reachables = []
        subdomains_mixed = []
        subdomain_quantity = len(subdomains)
        for subdomain in tqdm(subdomains):
            if custom_subdomains:
                if check_reachable(f"{subdomain}", timeout):
                    if verbose: tqdm.write(f"> {subdomain} is reachable.")
                    subdomains_reachables.append(f"{subdomain}")
                else:
                    if verbose: tqdm.write(f"> {subdomain} is not reachable.")
            else:
                if check_reachable(f"{subdomain}", timeout):
                    if verbose: tqdm.write(f"> {subdomain} is reachable.")
                    subdomains_reachables.append(f"{subdomain}")
                else:
                    if verbose: tqdm.write(f"> {subdomain} is not reachable.")
        subdomains_unreachables = [x for x in subdomains if x not in subdomains_reachables]
        for x in subdomains_reachables:
            subdomains_mixed.append((x+"."+target, True))
        for x in subdomains_unreachables:
            subdomains_mixed.append((x+"."+target, False))
        subdomains_mixed.sort()
        subdomains.clear()
        subdomains = [x[0][:-len(target)-1] for x in subdomains_mixed if x[1]]
        typer.echo(f"\n> Found {len(subdomains_reachables)}/{subdomain_quantity} reachable subdomains.") if verbose else ""
        typer.echo(subdomains) if verbose else ""
    if intitle:
        typer.echo(f"> Searching for subdomains containing '{intitle}' in its title...")
        matching_subdomains = []
        for subdomain in tqdm(subdomains):
            intitle_result = check_intitle(f"{subdomain}/{path_suffix}", intitle, verbose, timeout)
            if intitle_result:
                if verbose: tqdm.write(f"> Found {intitle} in '{subdomain}' title.")
                matching_subdomains.append(subdomain)
            else:
                if verbose: tqdm.write(f"> Not found {intitle} in '{subdomain}' title.")

        typer.echo(f"\n> Found {len(matching_subdomains)}/{len(subdomains)} subdomains matching the title '{intitle}'.") if verbose else ""
        typer.echo(matching_subdomains) if verbose else ""
        subdomains = matching_subdomains
        del matching_subdomains
    if inhtml:
        typer.echo(f"> Searching for subdomains containing '{inhtml}' in its HTML...")
        matching_subdomains = []
        for subdomain in tqdm(subdomains):
            inhtml_result = check_inhtml(f"{subdomain}/{path_suffix}", inhtml, verbose, timeout)
            if inhtml_result:
                if verbose: tqdm.write(f"> Found {inhtml} in '{subdomain}' HTML.")
                matching_subdomains.append(subdomain)
            else:
                if verbose: tqdm.write(f"> Not found {inhtml} in '{subdomain}' HTML.")
        typer.echo(f"\n> Found {len(matching_subdomains)}/{len(subdomains)} subdomains containing '{inhtml}' in its HTML.") if verbose else ""
        typer.echo(matching_subdomains) if verbose else ""
        subdomains = matching_subdomains
        del matching_subdomains
    if inurl:
        typer.echo(f"> Searching for subdomains containing '{inurl}' in its URL...")
        matching_subdomains = []
        for subdomain in tqdm(subdomains):
            inurl_result = check_inurl(f"{subdomain}/{path_suffix}", inurl, verbose)
            if inurl_result:
                if verbose: tqdm.write(f"> Found {inurl} in '{subdomain}' URL.")
                matching_subdomains.append(subdomain)
            else:
                if verbose: tqdm.write(f"> Not found {inurl} in '{subdomain}' URL.")
        typer.echo(f"\n> Found {len(matching_subdomains)}/{len(subdomains)} subdomains containing '{inurl}' in its URL.") if verbose else ""
        typer.echo(matching_subdomains) if verbose else ""
        subdomains = matching_subdomains
        del matching_subdomains
    # - Saving output (subdomain list) if needed
    if save_output:
        # IMPORT REMOVED - SAVE OUTPUT
        save_file(output_dir, target, output_format, check_reachability, verbose, subdomains, subdomains_mixed if check_reachability else None)
    # 3º Stage: Opening all tabs
    if open_tabs:
        tab_opener(subdomains, browser_executable, verbose, batch_size, subdomain_suffix, path_suffix, target)
    else:
        typer.echo(f"> Done!\n")


if __name__ == "__main__":
    app()

# TODO: *1.- Revise Options order. *2.- Add descriptions. 3.- Use https://docs.python.org/3/library/pathlib.html.
#  *4.- Add different output file formats. *5.- Add cookie capability. 6.- Maybe adding search engines mode is a good idea.
#  *7.- Add tables to verbose mode logs. *8.- Better solution to time.sleep(0). !9.- Fix bad output when only one subdomain bug.
#  10.- Add custom subdomain list file capability. 11.- Optimize with bs4 subdomain scraping. *12.- Check reachability.
#  13.- Make this more script-friendly. 14.- Maybe URL prefix is a good idea. 15.- Add crt.sh source.
#  16.- Add Firefox support and fix other browsers. 17.- Add auto 'Results' folder creation capability.
#  18.- Add support for multiple targets. 19.- Add support for bruteforcing target with wordlists. *20.- Add no-open-tabs mode.
#  21.- Add filtering subdomains by custom response codes. 22.- Add support for only opening websites with specific text in its HTML.
#  23.- Add threading support. 24.- Add host-to-ip capability. 25.- Add capability to open only subdomains added after any date.
#  26.- Add only open tabs which specific favicon coincide. 27.- Remove multiple in* capability. 28.- Add analysis on redirected links capability.
