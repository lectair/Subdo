import subprocess
import time
import os
import typer
import sys


def batch_opener(batch, batch_number, batches_size, browser_executable, subdomain_suffix, path_suffix, verbose):
    for subdomain in batch:
        action = "r"
        while action == "r":
            command = f'"{browser_executable}" {subdomain}{"."+subdomain_suffix+"." if subdomain_suffix else ""}/{path_suffix if path_suffix else ""}'
            os.system(command)
            if verbose: typer.echo("- " + command)
            typer.echo(f"\nBatch {str(batch_number + 1)}/{str(batches_size)} opened.")
            action = input("Options: [N] Next batch | [r] Repeat current batch | [q] Quit: ")
            if action.lower() == "q":
                sys.exit(1)
            elif len(action) == 0:
                pass
            else:
                typer.echo("\nInvalid option!")
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


def tab_opener(subdomains, browser_executable, verbose, batch_size, subdomain_suffix, path_suffix, target):
    command = f'"{browser_executable}"'
    subprocess.Popen(command)
    time.sleep(0.5)
    if verbose: typer.echo("\n> Start opening tabs.\n> COMMANDS LOG:")
    if batch_size != 0:
        batches = []
        batch_number = 0
        for subdomain in range(0, len(subdomains), batch_size):
            batch = subdomains[subdomain:subdomain + batch_size]
            batches.append(batch)
        batches_size = len(batches)
        for batch in batches:
            batch_opener(batch, batch_number, batches_size, browser_executable, subdomain_suffix, path_suffix, verbose)
    else:
        for subdomain in subdomains:
            command = f'"{browser_executable}" {subdomain}{"."+subdomain_suffix + "." if subdomain_suffix else ""}/{path_suffix if path_suffix else ""}'
            os.system(command)
            if verbose: typer.echo("- " + command)
    if verbose: typer.echo("\n> Finished opening tabs.")
    typer.echo(f"> Done! If tabs didn't open, launch the browser manually before running the script.\n")
