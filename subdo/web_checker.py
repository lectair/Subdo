import requests
import sys
import typer
import mmh3
import codecs
import warnings
from bs4 import BeautifulSoup as bs4

warnings.filterwarnings("ignore")


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
            return True
        else:
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
            return True
        else:
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
        return True
    else:
        return False


def check_favicon(target: str, favicon_hash: str, verbose: int, timeout: int) -> bool:
    """
    Check if target matches favicon hash.
    """
    try:
        response = requests.get('http://'+target, timeout=timeout, verify=False)
        data_shodan = bs4(response.text, 'html.parser')
        possible_elements = data_shodan.find_all("link", {"rel": "icon"})
        for element in possible_elements:
            if 'rel="icon"' in str(element):
                favicon_url = str(element).split('href="')[1].split('"')[0]
                if not target in favicon_url and not 'http://' in favicon_url and not 'https://' in favicon_url:
                    favicon_url = 'http://'+target+favicon_url
                current_hash = str(mmh3.hash(codecs.encode(requests.get(favicon_url, timeout=timeout, verify=False).content, "base64")))
        if current_hash == favicon_hash:
            return True
        else:
            return False
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        typer.echo(f"> ERROR CHECKING FAVICON: {e}") if verbose == 3 else ""
