![Subdo2_1_800x](https://user-images.githubusercontent.com/59050136/171484315-06d7a9de-c6bd-434d-b74e-29347eb8c65f.png)

# Subdo
Subdo is a Pentesting/OSINT software that automates the enumeration, verification and analysis of subdomains, using public registries such as Shodan or crt.sh.

## What can you do?
Subdo allows you to retrieve the subdomains of any website thanks to public DNS records.
These subdomains can then be saved in different formats or opened in the browser of your choice. You can open them in batches if there are many, check their reachability, filter by title, by containing a string in the whole html, by containing a string in its url, by matching the favicon, etc.
In total there are 19 parameters you can tweak, see them in the `Parameters` section.

## How it works?
Subdo obtains this data, for the moment, from two different sources: Shodan (needs a free API key if you make a lot of requests) and Crt.sh.

# Getting Started
## Prerequisites
Before using this tool you have to install the requirements.

`pip install -r requirements.txt`

## Usage
Subdo is a Typer-based tool, so it is an interactive tool. You can see all available parameters by entering the following:

`python3 main.py --help`

![screenshot_1_x600_1_x500](https://user-images.githubusercontent.com/59050136/190322632-cac362d1-201a-4e6d-975f-5417d5c16cf5.png)



**Here's a full example of a command:**

`python3 main.py --target verizon.com --inhtml swagger --save-output --output-format csv`

Here we search the verizon.com domain for subdomains that contain 'swagger' in their HTML code. 'Swagger' is the name of a famous CMS for interactive API documentation. This can reveal backdoors if someone has left these services public. It then saves the results in a csv file format.

**Another example command:**

`python3 main.py --target sony.com --check-reachability --inurl api --open-tabs --browser epic --batch-size 8 --verbose 2`


Here we search the domain sony.com for subdomains containing 'api' in their url. As in the previous example, this can help to find APIs. Then open the results in the epic browser, in batches of 8, useful for when there are too many subdomains to open them all at once.

**Tip:** Replace the cookie in the 'shodan-cookie.txt' file with your own so that you do not need to enter the cookie parameter every time you want to run the program

# Screenshots
![11_70](https://user-images.githubusercontent.com/59050136/190334512-949d348c-bb05-4fd5-9b5a-2d9594d86189.png)
![222_70_1_614x](https://user-images.githubusercontent.com/59050136/190334530-93ebace9-642b-40b7-a878-285cbb48c66d.png)  
![Captura_de_pantalla_2022-09-15_085312_614x](https://user-images.githubusercontent.com/59050136/190335282-19350477-33d6-4ba6-b543-d6d1deac3f76.png)


# Parameters
**Here are all the available parameters:**

`--target  TEXT`: **Target URL.** [default: None]

`--browser  TEXT`: **The browser to use for opening subdomains in tabs. Options: chrome, opera, edge, ie, epic, custom.** [default: chrome]

`--browser-executable  TEXT`: **Provide a custom browser executable if needed.** [default: None]

`--shodan-cookie  TEXT`: **The cookie to use for the Shodan scraping. If used only sometimes it's not needed.** [default: None]

`--path-sufix  TEXT`: **The URL path suffix to use. Example: /robots.txt.** [default: None]

`--subdomain-suffix  TEXT`: **The subdomain suffix to use. Example: .test -> subdomain.test.google.com.** [default: None]

`--check-reachability  --no-check-reachability`: **Check if the hosts are reachable. If so, only save and open the reachable ones. If output-format isn't 'txt' the output will save both but will have a column for reachability. WARNING: This will expose your IP to the host.** [default: no-check-reachability]

`--open-tabs  --no-open-tabs`: **Open the subdomains in browser tabs.** [default: no-open-tabs]

`--save-output  --no-save-output`: **Whether or not to save the subdomain list. If selected, the output will be saved to a file within the '.\Results' folder.** [default: no-save-output]

`--output-format  TEXT`: **The format to save the output. Options: txt, csv, json.** [default: txt]

`--output-dir  TEXT`: **The directory to save the output.** [default: .\ ]

`--batch-size  INTEGER`: **Open tabs in batch. Set this number to how many tabs you want to open at once.** [default: 0]

`--custom-subdomains  TEXT`: **Provide a file containing subdomains.** [default: None]

`--intitle  TEXT`: **Match only subdomains containing provided title.** [default: None]

`--inhtml  TEXT`: **Match only subdomains containing provided string in whole response.** [default: None]

`--inurl  TEXT`: **Match only subdomains containing provided string in URL.** [default: None]

`--favicon  TEXT`: **Match only subdomains with provided favicon hash.** [default: None]

`--timeout  INTEGER`: **Set timeout for subdomain requests.** [default: 5]

`--verbose  INTEGER`: **The verbosity level.** [default: 0]

`--help`: **Shows help message and exit.**

# [TO-DO]
There are a lot of things still to be fixed, added and modified. If you want to see all the TODO's in the main.py file at the bottom is the TODO list.
The list is out of sync with work, I will try to fix this soon.

If you fix or improve anything send me a pull request and I will gladly accept it.

# Author

Made with ❤️ by Lucas Klein for the open-soruce community.

# License

This project is licensed under the MIT License - see the LICENSE file for details
