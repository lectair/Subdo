import datetime
import typer
import json


def save_file(output_dir, target, output_format, check_reachability, verbose, subdomains, subdomains_mixed=None):
    with open(f'{output_dir}\\Results\\{target} {str(datetime.datetime.now())[:-7].replace(":", "-")}.{output_format}',
              'a', encoding='utf-8') as output_file:
        if verbose: typer.echo(
            f'\n> Saving output to "{output_dir}\\Results\\{target} {str(datetime.datetime.now())[:-7].replace(":", "-")}.{output_format}"')
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
                typer.echo(
                    "> Warning: CSV output is the same as TXT without enabling the check-reachability parameter. Using it anyways...")
                for x in subdomains:
                    output_file.write(f"{x}\n")
            elif output_format == "json":
                subdomains_json_temp = []
                for x in subdomains:
                    subdomains_json_temp.append(x + "." + target)
                output_file.write(f"{json.dumps(subdomains_json_temp, indent=4)}\n")
