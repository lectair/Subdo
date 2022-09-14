import subprocess
import time
import os
import typer
import sys


def batch_opener(batch, batch_number, batches_size, browser_executable, subdomain_suffix, path_suffix, target, verbose):
    print(batch_number)
    while action != "r" and action != "n" and action != "q":
        for subdomain in batch:
            command = f'"{browser_executable}" {subdomain}.{subdomain_suffix + "." if subdomain_suffix else ""}{target}/{path_suffix if path_suffix else ""}'
            os.system(command)
            if verbose: typer.echo("- " + command)
        typer.echo(f"\nBatch {str(batch_number + 1)}/{str(batches_size)} opened.")
        if batch_number + 1 != batches_size:
            action = input("Options: [N] Next batch | [r] Repeat current batch | [q] Quit: ")
            print()
            print(action)
            if action.lower() == "q":
                sys.exit(1)
            elif action.lower() == "r":
                pass
            elif (action.lower() == "n") or (len(action) == 0):
                print(batch)
                if batch_number + 1 == batches_size:
                    if verbose: typer.echo("\n> Finished opening tabs.")
                    typer.echo(
                        f"> Done! If tabs didn't open, launch the browser manually before running the script.\n")
                    sys.exit(1)
                else:
                    batch_number += 1
                    print(batch_number)
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


def tab_opener(subdomains, browser_executable, verbose, batch_size, subdomain_suffix, path_suffix, target):
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
            batch_opener(batch, batch_number, batches_size, action, browser_executable, subdomain_suffix, path_suffix, target, verbose)
    else:
        for subdomain in subdomains:
            command = f'"{browser_executable}" {subdomain}{"."+subdomain_suffix + "." if subdomain_suffix else ""}/{path_suffix if path_suffix else ""}'
            os.system(command)
            if verbose: typer.echo("- " + command)
    if verbose: typer.echo("\n> Finished opening tabs.")
    typer.echo(f"> Done! If tabs didn't open, launch the browser manually before running the script.\n")
