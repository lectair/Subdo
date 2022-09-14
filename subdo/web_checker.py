import requests
import sys
import typer


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
