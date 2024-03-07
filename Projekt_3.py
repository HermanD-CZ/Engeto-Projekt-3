"""
Projekt_3-Elections Scraper.py: třetí projekt do Engeto Online Python Akademie
author: David Herman
email: david.herman@seznam.cz
discord: DavidHerman5014
"""

import sys
import requests
import asyncio
import httpx
import bs4
import csv
from timeit import default_timer as timer




def check_the_arguments(arguments: list) -> None:
    """
    The function checks if the script is run with two mandatory arguments. 
    The first argument must be the URL and the second the name of the csv file. 
    Without the arguments, the script is terminated.
    """
    if len(arguments) != 3:
        print("""Mandatory arguments are missing to run the script. 
There are two mandatory arguments. The first is the url address 
and the second is the name of the csv output file.""")
        quit()

    elif  not arguments[1].startswith("http"):
        print("The first mandatory argument is not a url")
        quit()

    elif not arguments[2].endswith(".csv"):
        print("The second mandatory argument is not the csv file name")
        quit()

    else:
        print("The script is running")

def get_server_response(url: str) -> str:
    """
    Return the server response to a GET request.
    """
    return requests.get(url)

async def get_server_responses_async(urls: list):
    """
    Return the server response to a asynchro GET request.
    """
    async with httpx.AsyncClient() as client:
        requests_ = [client.get(url) for url in urls]  
        responses = await asyncio.gather(*requests_)        
    return responses
    

def parse_server_response(response: str) -> bs4.BeautifulSoup:
    """
    Get a split response to a GET request.
    """
    return bs4.BeautifulSoup(response.content, features="html.parser")

def find_selected_tags(tag:str, parsed_response: bs4.BeautifulSoup, name_class = "") -> bs4.element.ResultSet:
    """
    Find all selected tags from the page source code. For more specific searches, the class name can be selected.
    """
    return parsed_response.find_all(tag, {"class": name_class}) 

def get_municipality_numbers(parsed_response: bs4.BeautifulSoup) -> list:
    """
    Get list of municipality numbers.
    """
    municipality_numbers_list = []
    municipality_numbers = find_selected_tags("td", parsed_response, "cislo")
    
    for number in range(len(municipality_numbers)):
        municipality_numbers_list.append(municipality_numbers[number].get_text())
    return municipality_numbers_list

def get_municipality_names(server_responses:list) -> list:
    """
    Get list of municipality names.
    """
    municipalitiy_names_list = []
    
    for number in range(len(server_responses)):
        h3_tags = find_selected_tags("h3", parse_server_response(server_responses[number]))
        subdata = []
                
        for num in range(len(h3_tags)): 
            subdata.append(h3_tags[num].get_text().strip("\n"))
        municipalitiy_names_list.append(subdata[2][6:])
    return municipalitiy_names_list
    
def get_links_for_municipalities(parsed_response: bs4.BeautifulSoup) -> list:
    """
    Get list of links for each municipality.
    """
    links_list = []
    links = find_selected_tags("a", parsed_response)
    
    for link in links: # Find all links from the page source code.
        links_list.append(link.get('href'))
    
    clear_links_list = []
    
    for link in links_list: # Select the correct links for municipalities
        if "ps311" in link and sys.argv[1][:31] + link not in clear_links_list: # Clear list from duplicity
                clear_links_list.append(sys.argv[1][:31] + link) # Add links to the list
    return clear_links_list

def get_data_for_municipalities(server_responses:list) -> list:
    """
    Get resulting data for municipalities.
    """
    data = []
    
    for number in range(len(server_responses)):
        td_tags_cislo = find_selected_tags("td", parse_server_response(server_responses[number]),"cislo")
        subdata = []
                
        for num in range(len(td_tags_cislo)): # get data from web table and replace signs "\xa0" for "". Thousands are thus not separated from the rest by any sign.
            subdata.append(td_tags_cislo[num].get_text().replace("\xa0", ""))
        data.append(subdata)
    return data

def get_names_of_parties(server_responses: bs4.BeautifulSoup) -> list:
    """
    Get names of the parties standing for election.
    """
    names_of_parties = []
    td_tags_overflow_name = find_selected_tags("td", parse_server_response(server_responses[0]),"overflow_name")
    
    for number in range(len(td_tags_overflow_name)):
        names_of_parties.append(td_tags_overflow_name[number].get_text())
    return names_of_parties


def write_data_to_csv( file_name: str) -> csv:
    """
    Selects the data and writes it to a file
    """
    main_parsed_response = parse_server_response(get_server_response(sys.argv[1]))
    url_list = get_links_for_municipalities(main_parsed_response)
    server_responses = asyncio.run(get_server_responses_async(url_list))
    munic_numbers = get_municipality_numbers(main_parsed_response)
    munic_names = get_municipality_names(server_responses)
    parties_names = get_names_of_parties(server_responses)
    data = get_data_for_municipalities(server_responses)
    data_for_writing = []
    data_for_writing.append(["Code", "Name", "Registered", "Envelopes", "Valid"] + parties_names)
    
    for number in range(len(url_list)):
        data_for_writing.append([munic_numbers[number], munic_names[number], 
                                 data[number][3], data[number][4], data[number][7]] + data[number][10::3])
       
    with open(file_name, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(data_for_writing)
    
    print(f"The file {file_name} has been created and the data written to it.")
          
if __name__ == "__main__":
       
    start = timer()   
    check_the_arguments(sys.argv)  
    write_data_to_csv(sys.argv[2]) 
    end = timer()
    elapsed_time = round(((end - start) / 60), 1)  
    print(f"It took {elapsed_time} min") 
   