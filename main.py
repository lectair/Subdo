import datetime
import os
import subprocess
import sys
import requests
import time
import urllib.parse
import typer
import json
#import threading
from subprocess import Popen
from os.path import exists as file_exists
from typing import Optional
from rich.console import Console
from rich.table import Table
from bs4 import BeautifulSoup as bs4

requests.packages.urllib3.disable_warnings()

app = typer.Typer(add_completion=False)
console = Console()


def check_reachable(target: str, timeout: int) -> bool:
    """
    Check if a target is reachable.
    """
    try:
        requests.get('http://'+target, timeout=timeout, verify=False)
        return True
    except KeyboardInterrupt:
        sys.exit(1)
    except:
        return False


def check_intitle(target: str, string: str, verbose: int, timeout: int) -> bool:
    """
    Check if target title contains specific string.
    """
    try:
        response = requests.get('http://'+target, timeout=timeout, verify=False).text.lower()
        if string.lower() in response.split("<title>")[1].split("</title>")[0]:
            typer.echo(f"> Found {string} in '{target}' title.") if verbose else ""
            return True
        else:
            typer.echo(f"> Not found {string} in '{target}' title.") if verbose == 2 else ""
            return False
    except KeyboardInterrupt:
        sys.exit(1)
    except IndexError:
        return False
    except ConnectionError:
        return False
    except Exception as e:
        typer.echo(f"> Not found {string} in '{target}' title.") if verbose == 2 else ""
        typer.echo(f"> ERROR CHECKING INTITLE: {e}") if verbose == 3 else ""


def check_inhtml(target: str, string: str, verbose: int, timeout: int) -> bool:
    """
    Check if target HTML contains specific string.
    """
    try:
        response = requests.get('http://'+target, timeout=timeout, verify=False).text.lower()
        if string.lower() in response:
            typer.echo(f"> Found {string} in '{target}' HTML.") if verbose else ""
            return True
        else:
            typer.echo(f"> Not found {string} in '{target}' HTML.") if verbose == 2 else ""
            return False
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        typer.echo(f"> ERROR CHECKING INHTML: {e}") if verbose == 3 else ""


def check_inurl(target: str, string: str, verbose: int) -> bool:
    """
    Check if target URL contains specific string.
    """
    if string.lower() in target:
        typer.echo(f"> Found {string} in '{target}' URL.") if verbose else ""
        return True
    else:
        typer.echo(f"> Not found {string} in '{target}' URL.") if verbose == 2 else ""
        return False


def batch_opener(batch, batch_number, batches_size, browser_executable, subdomain_suffix, path_suffix, target, verbose):
    while True:
        for subdomain in batch:
            command = f'"{browser_executable}" {subdomain}.{subdomain_suffix + "." if subdomain_suffix else ""}{target}/{path_suffix if path_suffix else ""}'
            os.system(command)
            if verbose: typer.echo("- " + command)
        typer.echo(f"\nBatch {str(batch_number + 1)}/{str(batches_size)} opened.")
        if batch_number + 1 != batches_size:
            action = "x"
            while action != "r" and action != "n" and action != "q":
                action = input("Options: [N] Next batch | [r] Repeat current batch | [q] Quit: ")
                print()
                if action.lower() == "q":
                    sys.exit(1)
                elif action.lower() == "r":
                    continue
                elif (action.lower() == "n") or (len(action) == 0):
                    if batch_number + 1 == batches_size:
                        if verbose: typer.echo("\n> Finished opening tabs.")
                        typer.echo(
                            f"> Done! If tabs didn't open, launch the browser manually before running the script.\n")
                        sys.exit(1)
                    batch_number += 1
                    break
                else:
                    action = "x"
                    typer.echo("\nInvalid option!")
        else:
            if verbose: typer.echo("\n> Finished opening tabs.")
            typer.echo(
                f"> Done! If tabs didn't open, launch the browser manually before running the script.\n")
            sys.exit(1)


'''def thread_creator(function, thread_quantity, target, timeout):
    threads = []
    for i in range(thread_quantity):
        thread = threading.Thread(target=function, args=(target, timeout))
        threads.append(thread)
        thread.start()

    print(threads)'''


@app.command()
def main(target: str,
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
         custom_subdomains: int = typer.Option(None, help="Provide a file where subdomains are already found."),
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
    if ("http://" in target) or ("https://" in target):
        target = target.split("://")[1]
    if file_exists('shodan-cookie.txt') and not shodan_cookie:
        shodan_cookie = open('shodan-cookie.txt', 'r', encoding='utf-8').read().rstrip()
    browser_executable = browser_executables[browser]
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
        table.add_row("In Title", intitle)
        table.add_row("In HTML", inhtml)
        table.add_row("In URL", inurl)
        table.add_row("Timeout", str(timeout))
        #table.add_row("Threads", str(threads))
        table.add_row("Verbosity Level", str(verbose))
        console.print(table)
        time.sleep(1)
    # 2º Stage: Scraping subdomains and manipulating them
    # - Shodan
    if verbose:
        typer.echo("> Start Shodan scraping for subdomains.")
        time.sleep(1)
    response = requests.get(f"https://www.shodan.io/domain/{target}", headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
        'Cookie': f'polito="{shodan_cookie}"'}).text
    if verbose:
        if verbose == 3:
            with open('last_shodan_scrape.html', 'w', encoding='utf-8') as shodan_file:
                shodan_file.write(response)
            typer.echo("> START SHODAN HTML RESPONSE:")
        typer.echo(
            f"{bs4(response, 'html.parser').prettify()}\n\n> END SHODAN HTML RESPONSE\n> Finished Shodan scraping.") if verbose == 3 else typer.echo(
            "> Finished Shodan scraping.")
    try:
        shodan_subdomains = response.lower().split('<ul id="subdomains">')[1].split('</ul>')[0].split('</li>\n<li>')
        shodan_subdomains[0], shodan_subdomains[-1] = shodan_subdomains[0][5:], shodan_subdomains[-1][:-6]
    except IndexError:
        typer.echo("> Error scraping subdomains from Shodan.\nMaybe the target doesn't exist? Or you did not enter the cookie?\nTip: Switch verbosity to 2 to see the HTML response.\n")
        shodan_subdomains = []
    if verbose: typer.echo(f"> Found {len(shodan_subdomains)} subdomains in Shodan.")
    # - Crt.sh
    if verbose:
        typer.echo("> Start crt.sh scraping for subdomains.")
        time.sleep(1)
    response = requests.get(f"https://crt.sh/?q={target}").text.lower()
    if verbose:
        if verbose == 3:
            with open('last_crt_scrape.html', 'w', encoding='utf-8') as crt_file:
                crt_file.write(response)
            typer.echo("> START CRT.SH JSON RESPONSE:")
        typer.echo(
            f"{bs4(response, 'html.parser').prettify()}\n\n> END CRT.SH JSON RESPONSE\n> Finished Crt.sh scraping.") if verbose == 3 else typer.echo(
            "> Finished Crt.sh scraping.")
    try:
        crt_subdomains = []
        '''
        soup = bs4(response.lower(), 'html.parser')
        alltds = soup.find_all("td")
        print(alltds[0].text.split("\n"))
        for x in alltds:
            if target in x:
                crt_subdomains.append(x.text)
        print(crt_subdomains)
        '''
        for line in response.splitlines():
            if "<td>" in line:
                if target in line:
                    if "*" not in line:
                        subdomain = line.split("<td>")[1].split("</td>")[0]
                    if "\n" in line:
                        subdomain = line.split("\n")[0]
                    if "\n" in line:
                        subdomain = line.split("\n")[1]
                    if "<" in line:
                        subdomain = line.split("<")[0]
                    if "<" in line:
                        subdomain = line.split("<")[0]
                    if ">" in line:
                        subdomain = line.split(">")[1]
                    if ">" in line:
                        subdomain = line.split(">")[1]
                    if "</li>" in line:
                        subdomain = line.split("</li>")[0]
                    if "<li>" in line:
                        subdomain = line.split("<li>")[0]
                    crt_subdomains.append(subdomain[:-len(target)-1])
        crt_subdomains = list(set(crt_subdomains))
    except IndexError:
        typer.echo("> Error scraping subdomains from crt.sh. Aborted!\nMaybe the target doesn't exist?\n\nTip: Switch verbosity to 2 to see the HTML response.")
        sys.exit(1)
    if verbose: typer.echo(f"> Found {len(crt_subdomains)} subdomains in crt.sh.")
    # -- Finished scraping
    subdomains = sorted(list(filter(None, list(set(shodan_subdomains + crt_subdomains)))))
    if verbose:
        typer.echo(f"> Found {len(subdomains)} unique subdomains in total.")
        typer.echo(subdomains)
        print()
    if check_reachability:
        '''if threads > 1:
            subdomains_reachables = []
            subdomains_mixed = []
            subdomain_quantity = len(subdomains)
            for subdomain in subdomains:
                if thread_creator(check_reachability,threads,subdomain,timeout):
                    if verbose: typer.echo(f"> {subdomain}.{target} is reachable.")
                    subdomains_reachables.append(f"{subdomain}")
                else:
                    if verbose: typer.echo(f"> {subdomain}.{target} is not reachable.")
            subdomains_unreachables = [x for x in subdomains if x not in subdomains_reachables]
            for x in subdomains_reachables:
                subdomains_mixed.append((x+"."+target, True))
            for x in subdomains_unreachables:
                subdomains_mixed.append((x+"."+target, False))
            subdomains_mixed.sort()
            subdomains.clear()
            subdomains = [x[0][:-len(target)-1] for x in subdomains_mixed if x[1]]
            typer.echo(f"\n> Found {len(subdomains_reachables)}/{subdomain_quantity} reachable subdomains.") if verbose else ""
            typer.echo(subdomains) if verbose else ""'''
        #else:
        subdomains_reachables = []
        subdomains_mixed = []
        subdomain_quantity = len(subdomains)
        for subdomain in subdomains:
            if check_reachable(f"{subdomain}.{target}", timeout):
                if verbose: typer.echo(f"> {subdomain}.{target} is reachable.")
                subdomains_reachables.append(f"{subdomain}")
            else:
                if verbose: typer.echo(f"> {subdomain}.{target} is not reachable.")
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
        typer.echo("> Searching for subdomains in title...")
        matching_subdomains = []
        for subdomain in subdomains:
            if check_intitle(f"{subdomain}.{target}/{path_suffix}", intitle, verbose, timeout):
                matching_subdomains.append(subdomain)
        typer.echo(f"\n> Found {len(matching_subdomains)}/{len(subdomains)} subdomains matching the title '{intitle}'.") if verbose else ""
        typer.echo(matching_subdomains) if verbose else ""
        subdomains = matching_subdomains
        del matching_subdomains
    if inhtml:
        typer.echo("> Searching for subdomains in HTML...")
        matching_subdomains = []
        for subdomain in subdomains:
            matching_subdomains.append(subdomain) if check_inhtml(f"{subdomain}.{target}/{path_suffix}", inhtml, verbose, timeout) else ""
        typer.echo(f"\n> Found {len(matching_subdomains)}/{len(subdomains)} subdomains containing '{inhtml}' in its HTML.") if verbose else ""
        typer.echo(matching_subdomains) if verbose else ""
        subdomains = matching_subdomains
        del matching_subdomains
    if inurl:
        typer.echo("> Searching for subdomains in URL...")
        matching_subdomains = []
        for subdomain in subdomains:
            if check_inurl(f"{subdomain}.{target}/{path_suffix}", inurl, verbose):
                matching_subdomains.append(subdomain)
        typer.echo(f"\n> Found {len(matching_subdomains)}/{len(subdomains)} subdomains containing '{inurl}' in its URL.") if verbose else ""
        typer.echo(matching_subdomains) if verbose else ""
        subdomains = matching_subdomains
        del matching_subdomains
    # - Saving output (subdomain list) if needed
    if save_output:
        with open(f'{output_dir}\\Results\\{target} {str(datetime.datetime.now())[:-7].replace(":", "-")}.{output_format}',
                  'a', encoding='utf-8') as output_file:
            if verbose: typer.echo(f'\n> Saving output to "{output_dir}\\Results\\{target} {str(datetime.datetime.now())[:-7].replace(":", "-")}.{output_format}"')
            if check_reachability:
                if output_format == "txt":
                    for x in subdomains:
                        output_file.write(f"{x}\n")
                elif output_format == "csv":
                    output_file.write(f"subdomain,is_reachable\n")
                    for x in subdomains_mixed:
                        output_file.write(f"{x[0]},{x[1]}\n")
                elif output_format == "json":
                    output_file.write(f"{json.dumps(subdomains_mixed, indent=4)}\n")
            else:
                if output_format == "txt":
                    for x in subdomains:
                        output_file.write(f"{x}\n")
                elif output_format == "csv":
                    typer.echo("> Warning: CSV output is the same as TXT without enabling the check-reachability parameter. Using it anyways...")
                    for x in subdomains:
                        output_file.write(f"{x}\n")
                elif output_format == "json":
                    subdomains_json_temp = []
                    for x in subdomains:
                        subdomains_json_temp.append(x+"."+target)
                    output_file.write(f"{json.dumps(subdomains_json_temp, indent=4)}\n")

    # 3º Stage: Opening all tabs
    if open_tabs:
        command = f'"{browser_executable}"'
        subprocess.Popen(command)
        time.sleep(0.5)
        if verbose: typer.echo("\n> Start opening tabs.\n> COMMANDS LOG:")
        if batch_size != 0:
            batches = []
            batch_number = 0
            action = "r"
            for subdomain in range(0, len(subdomains), batch_size):
                batch = subdomains[subdomain:subdomain + batch_size]
                batches.append(batch)
            batches_size = len(batches)
            for batch in batches:
                batch_opener(batch, batch_number, batches_size, browser_executable, subdomain_suffix, path_suffix, target, verbose)
        else:
            for subdomain in subdomains:
                command = f'"{browser_executable}" {subdomain}.{subdomain_suffix + "." if subdomain_suffix else ""}{target}/{path_suffix if path_suffix else ""}'
                os.system(command)
                if verbose: typer.echo("- " + command)
        if verbose: typer.echo("\n> Finished opening tabs.")
        typer.echo(f"> Done! If tabs didn't open, launch the browser manually before running the script.\n")
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
