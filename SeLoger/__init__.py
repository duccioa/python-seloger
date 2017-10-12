from bs4 import BeautifulSoup
from unicodedata import normalize
import re
import requests
from requests.exceptions import RequestException
from time import sleep
from pathlib import Path
import pandas as pd


def requests_get(*args, **kwargs):
    """
    Retries if a RequestException is raised (could be a connection error or
    a timeout).
    """

    logger = kwargs.pop('logger', None)
    s = requests.Session()
    s.headers[
        'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'

    try:
        return s.get(*args, **kwargs)
    except RequestException as exc:
        if logger:
            logger.warning('Request failed (%s). Retrying ...', exc)
        return s.get(*args, **kwargs)


def create_param_url(search_params: dict):
    url_string = ""
    for key, value in search_params.items():
        url_string = url_string + "&" + key + "=" + value
    return url_string


def print_results(results: dict):
    print(f"** Annonce {results['idannonce']} **")
    for key, value in results.items():
        print(f"'{key}': '{value}'")
    print("\n\n")


class SelogerBase(object):
    """
    Base class for all Seloger wrapper

    Parameters
    ----------
    class_filters : dict
        Main search options
        ex. {'transaction_type':['achat'], 'bien': ['appartement', 'maison'], 'naturebien': ['ancien', 'neuf']}
    type_of_search: str
        Can be either 'base', for ads of properties on the market, or 'biens-vendus' for the search on the property sold section.
    location : dict
        Either one of the following:
        postcode (ex. {'code_postal': 75015} or {'code_postal': 75})
        INSEE code (ex. {'code_INSEE': 75115})
        Location name (ex. {'location_name': 'PARIS'})
    *argv : str
        Search options from binary_filter_options
    **kwargs: dict ex.{'delay': 2}
        Other search options or tweaking parameters
        delay: number of seconds between requests, used to avoid overcharging servers
    Returns
    -------


    """

    def __init__(self, **kwargs):
        # Get parameters
        self.delay = kwargs.get('delay') or 3

    def get_current_parameters(self, search_url=True, *args, **kwargs):
        """
        Retrieve search parameters from the html page of a search on Seloger.com
        :param search_url: The page url is passed as an input (True) or a parsed page (False).
        :param args: A BeautifulSoup parsed page.
        :param kwargs:
            write_to: a string with the path and name of a file to save the html of the url or the parsed page.
        :return: a dictionary with the search parameters as they appear in the json of html page.
        """

        if search_url:
            try:
                print(f"Get pages from base url {self.url}\n", "...")
                page0 = requests_get(self.url)
                print("Request successful.")
            except:
                print('ERROR: too many redirects - They might have detected the crawler, try changing ip.')
                return

            print("Parsing page\n", "...")
            page_parsed = BeautifulSoup(page0.content, 'html.parser')

            # Check validity of the page
            try:
                if page_parsed.find('meta').attrs['name'] == 'robots':
                    print('ERROR: invalid result page - They might have detected the crawler, try changing ip.')
                    return
            except KeyError:
                print(f"Valid response from {self.url}")
        else:
            page_parsed = args[0]

        write_to = kwargs.get('write_to')

        # Save html to file

        if write_to:
            my_file = Path(write_to)
            if my_file.is_file():
                print(f"{write_to} exists already. Do you want to overwrite?\n")
                response = input("Y/N > ")
                if response == 'Y' or response == 'y':
                    write_to_sure = write_to
                else:
                    print("Please, give type another file path:\n")
                    response = input("new path to file > ")
                    write_to_sure = response
            with open(write_to_sure, 'w+') as file:
                file.write(page_parsed.text)

        # Extact the json from the JavaScript of the page
        page_data = page_parsed.find('div', {'class': 'c-wrap-main'})
        page_data_str = normalize('NFKD', page_data.prettify())
        page_data_str_minified = page_data_str.replace('\n', '').replace('\r', '').replace(' ', '').replace("true",
                                                                                                            "True").replace(
            "false", "False")
        json_str = re.search('({.*});ava.*', page_data_str_minified).group(1)
        params = eval(json_str)
        return params

    def get_pages(self, **kwargs):
        """
        :param kwargs:
            max_num_pages: maximum number of pages to be processed. If left empty, it is set to its maximum number 100.
        :return: a generator of HTML parsed result pages.
        """
        max_num_pages = kwargs.get('max_num_pages') or 100
        results_per_page = 20

        try:
            print(f"Get pages from base url {self.url}\n", "...")
            page0 = requests_get(self.url)
            print("Request successful.")
        except:
            print('ERROR: too many redirects - They might have detected the crawler, try changing ip.')
            return

        print("Parsing page\n", "...")
        page_parsed = BeautifulSoup(page0.content, 'html.parser')

        # Check validity of the page
        try:
            if page_parsed.find('meta').attrs['name'] == 'robots':
                print('ERROR: invalid result page - They might have detected the crawler, try changing ip.')
                return
        except KeyError:
            print(f"Valid response from {self.url}")

        num_results = re.search('\s?"nbresults"\s+:\s? "(\d+[^"]*)"', page_parsed.text).group(1)
        num_results = int(num_results.replace("\xa0", ""))

        num_pages = num_results // results_per_page + 1

        if num_pages > max_num_pages:
            num_pages = max_num_pages

        print(f"The search returned {num_results} results.")
        print(f"{results_per_page*num_pages} results in {num_pages} pages will be processed.")

        current_page_num = int(re.search('\s?"nbpage"\s+:\s? "(\d+[^"]*)"', page_parsed.text).group(1))

        while current_page_num <= num_pages:

            if current_page_num == 1:
                current_page_parsed = page_parsed
                print(f"Page {current_page_num} parsed")

            else:
                current_page_url = self.url + "&LISTING-LISTpg=" + str(current_page_num)
                print(f"Get url {current_page_url}")
                sleep(self.delay)
                current_page = requests_get(current_page_url)
                current_page_parsed = BeautifulSoup(current_page.content, 'html.parser')
                print(f"Page {current_page_num} parsed")

            current_page_num += 1
            yield current_page_parsed

    def get_results(self, max_num_pages=None, **kwargs):
        """
        :param
        kwargs:
            pages: a generator created with get_pages(). This parameter overrides the other two.

        max_number_pages: int, if empty it is set to its maximum number 100.
        print_results: int, print a number per page of results for control.

        :return: A generator of dictionaries each corresponding to a property ad
        """
        pages = kwargs.get('pages')

        for page in pages or self.get_pages(max_num_pages=max_num_pages):

            params = self.get_current_parameters(False, page)
            properties = params['products']
            n = kwargs.get('print_results')
            printed_results = 0

            for ad in properties:
                if n:
                    while printed_results <= n:
                        print_results(ad)
                        printed_results += 1

                yield ad

    def results_to_dataframe(self, max_num_pages=None, **kwargs):

        results = kwargs.get('results')
        df = pd.DataFrame()
        for ad in results or self.get_results(max_num_pages=max_num_pages):
            d = pd.DataFrame.from_dict(ad)
            df = df.append(d)
        df.drop(['affichagetype', 'idtypepublicationsourcecouplage', 'produitsvisibilite'], axis=1, inplace=True)
        df.reset_index(inplace=True)
        df.drop('index', axis=1, inplace=True)
        for column in df.columns:
            if re.search("^nb", column) or column == 'prix' or column == 'surface':
                df[column] = pd.to_numeric(df[column].str.replace(',', '.'))

        return df


class SeLogerAchat(SelogerBase):
    def __init__(self, search_params):
        self.url = "http://www.seloger.com/list.htm?" + "idtt=2" + create_param_url(search_params=search_params)
        super(SeLogerAchat, self).__init__()


class SeLogerLocation(SelogerBase):
    def __init__(self, search_params):
        self.url = "http://www.seloger.com/list.htm?" + "idtt=1" + create_param_url(search_params=search_params)
        super(SeLogerLocation, self).__init__()


class SeLogerLocationTemporaire(SelogerBase):
    def __init__(self, search_params):
        self.url = "http://www.seloger.com/list.htm?" + "idtt=3" + create_param_url(search_params=search_params)
        super(SeLogerLocationTemporaire, self).__init__()


class SeLogerLocationViager(SelogerBase):
    def __init__(self, search_params):
        self.url = "http://www.seloger.com/list.htm?" + "idtt=5" + create_param_url(search_params=search_params)
        super(SeLogerLocationViager, self).__init__()


class SeLogerInvestissement(SelogerBase):
    def __init__(self, search_params):
        self.url = "http://www.seloger.com/list.htm?" + "idtt=6" + create_param_url(search_params=search_params)
        super(SeLogerInvestissement, self).__init__()


class SeLogerLocationVacances(SelogerBase):
    def __init__(self, search_params):
        self.url = "http://www.seloger.com/list.htm?" + "idtt=4" + create_param_url(search_params=search_params)
        super(SeLogerLocationVacances, self).__init__()


class SeLogerBiensVendus(SelogerBase):
    def __init__(self, search_params):
        self.url = "http://biens-vendus.seloger.com/list.htm?" + "idtt=4" + create_param_url(
            search_params=search_params)
        super(SeLogerBiensVendus, self).__init__()


# Show help for search filter options
def show_search_filters(**kwargs):
    def print_type_options(type_options):
        print("\n")
        for option_title, option_value in type_options.items():
            print("\t" + option_title + ":")
            print("\t-----")
            print("\t\t URL key:", "'" + option_value['url_key'] + "'")
            print("\t\t URL key options:")
            for option, option_api_value in option_value['value'].items():
                print("\t\t\t* " + option + ":", "'" + option_api_value + "'")
            search_example = option_value['example']
            print("\n")
            print("\t\tIf you want to", search_example['description'], search_example['url_key'])
            print("\n")

    def print_binary_and_numeric_options(search_options):
        print("\n")
        for option_title, option_value in search_options['Filters'].items():
            print("\t" + option_title + ":")
            print("\t-----")
            for option, option_api_value in option_value.items():
                print("\t\t\t* " + option + ":",
                      "\t{'" + option_api_value['url_key'] + "': " + "'" + option_api_value['value'] + "'}")
        search_example = amenities_and_ad_filters['example']
        print("\n")
        print("\t\tIf you want to", search_example['description'], search_example['url_key'])
        print("\n")

    def print_choice(selection_labels):
        print("What filters do you wnt to know about (quit with 'q')?")
        print(
            "1. Sort options \n2. Property types \n3. Price, size and number of rooms \n4. Kitchen and heating types \n5. Amenities and ad filters")
        sel = input(" > ")
        if sel == 'q':
            return
        print_search_filters = selection_labels[sel].get('fun')
        search_filters = selection_labels[sel].get('arg')
        print_search_filters(search_filters)
        print_choice(selection_labels)

    sort_by = {
        'Sorting options': {
            'url_key': 'tri',
            'value': {
                'By selection': 'initial',
                'By price': 'a_px',
                'By surface': 'a_surface',
                'By location': 'a_ville',
                'By date': 'd_dt_crea'
            },
            'example': {'description': 'sort the ads by creation date:',
                        'url_key': "{'tri': 'd_dt_crea'}"}
        }
    }

    property_type = {
        'Property type': {
            'url_key': 'idtypebien',
            'value': {
                'Apartment': '1',
                'House': '2',
                'Car park': '3',
                'Shop': '6',
                'Commercial': '7',
                'Office': '8',
                'Lofts - Ateliers - Land': '9',
                'Various': '10',
                'Property': '11',
                'Building': '12',
                'Castle': '13',
                'Hotels Particuliers': '14'
            },
            'example': {'description': 'look for houses and apartments only:',
                        'url_key': "{'idtypebien': '1,2'}"}
        },
        'Building age': {
            'url_key': 'naturebien',
            'value': {
                'old': '1',
                'New': '2',
                'In construction': '4'
            },
            'example': {'description': 'look for new construction only:',
                        'url_key': "{'naturebien': '2'}"}

        }
    }

    kitchen_and_heating_type = {
        'Kitchen type': {
            'url_key': 'idtypecuisine',
            'value': {
                'Separated kitchen': '3',
                'Open kitchen': '2',
                'Kitchenette': '5',
                'Fitted kitchen': '9'
            },
            'example': {'description': 'an open kitchen:',
                        'url_key': "{'idtypecuisine': '2'}"}
        },
        'Heating type': {
            'url_key': 'idtypechauffage',
            'value': {
                'individuel': '8192',
                'central': '4096',
                'electrique': '2048',
                'gaz': '512',
                'fuel': '1024',
                'radiateur': '128',
                'sol': '256'
            },
            'example': {'description': 'centralised underfloor heating:',
                        'url_key': "{'idtypechauffage': '4096, 256'}"}
        }
    }

    amenities_and_ad_filters = {
        'Filters': {
            'Ad options': {
                'Ad with video': {'url_key': 'video', 'value': '1'},
                'Ad with virtual visit': {'url_key': 'vv', 'value': '1'},
                'Ad with photos': {'url_key': 'photo', 'value': '15'},
                'Exclusive': {'url_key': 'si_mandatexclusif', 'value': '1'},
                'Price has changed': {'url_key': 'siBaissePrix', 'value': '1'}
            },
            'Amentities': {
                'Last floor': {'url_key': 'si_dernieretage', 'value': '1'},
                'Separated toilets': {'url_key': 'si_toilettes_separees', 'value': '1'},
                'Bath tube': {'url_key': 'nb_salles_de_bainsmin', 'value': '1'},
                'Bathroom': {'url_key': 'nb_salles_deaumin', 'value': '1'},
                'Separate entrance': {'url_key': 'si_entree', 'value': '1'},
                'Living room': {'url_key': 'si_sejour', 'value': '1'},
                'Dining room': {'url_key': 'si_salle_a_manger', 'value': '1'},
                'Terrace': {'url_key': 'si_terrasse', 'value': '1'},
                'Balcony': {'url_key': 'nb_balconsmin', 'value': 'Insert number as a string'},
                'Car park': {'url_key': 'si_parkings', 'value': '1'},
                'Car box': {'url_key': 'si_boxes', 'value': '1'},
                'Cellar': {'url_key': 'si_cave', 'value': '1'},
                'Fire place': {'url_key': 'si_cheminee', 'value': '1'},
                'Wooden floor': {'url_key': 'si_parquet', 'value': '1'},
                'Lift': {'url_key': 'si_ascenseur', 'value': '1'},
                'Swimming pool': {'url_key': 'si_piscine', 'value': '1'},
                'Built-in wardrobe': {'url_key': 'si_placards', 'value': '1'},
                'Interphone': {'url_key': 'si_interphone', 'value': '1'},
                'Security code': {'url_key': 'si_digicode', 'value': '1'},
                'Concierge': {'url_key': 'si_gardien', 'value': '1'},
                'Disable access': {'url_key': 'si_handicape', 'value': '1'},
                'Alarm': {'url_key': 'si_alarme', 'value': '1'},
                'Without vis-a-vis': {'url_key': 'si_visavis', 'value': '1'},
                'Nice view': {'url_key': 'si_vue', 'value': '1'},
                'South facing': {'url_key': 'si_sud', 'value': '1'},
                'Air conditioning': {'url_key': 'si_climatisation', 'value': '1'}
            }

        },
        'example': {'description': 'add a lift, a parking and the air conditioning.',
                    'url_key': "{'si_ascenseur': '1', 'si_climatisation': '1', 'si_parkings': '1'}"}

    }

    property_size = {
        'Filters': {
            'Property size': {
                'Minimum price': {'url_key': 'pxmin', 'value': 'Insert number as a string'},
                'Maximum price': {'url_key': 'pxmax', 'value': 'Insert number as a string'},
                'Minimum surface': {'url_key': 'surfacemin', 'value': 'Insert number as a string'},
                'Maximum surface': {'url_key': 'surfacemax', 'value': 'Insert number as a string'},
                'Number of rooms': {'url_key': 'nb_pieces', 'value': 'Insert number as a string'},
                'Lower floor': {'url_key': 'etagemin', 'value': 'Insert number as a string'},
                'Higher floor': {'url_key': 'etagemax', 'value': 'Insert number as a string'},
                'Number fo bedrooms': {'url_key': 'nb_chambres', 'value': 'Insert number as a string'},
                'Minimum land surface': {'url_key': 'surf_terrainmin', 'value': 'Insert number as a string'},
                'Maximum land surface': {'url_key': 'surf_terrainmax', 'value': 'Insert number as a string'}
            }
        },
        'example': {'description': 'look for a minimum surface of 70 sqm, 2 bedrooms for maximum 500 000 euros:',
                    'url_key': "{'surfacemin': '70', 'nb_chambres': '2', 'pxmax': '500000'}"}

    }

    selection_labels = {
        '1': {'fun': print_type_options, 'arg': sort_by},
        '2': {'fun': print_type_options, 'arg': property_type},
        '3': {'fun': print_binary_and_numeric_options, 'arg': property_size},
        '4': {'fun': print_type_options, 'arg': kitchen_and_heating_type},
        '5': {'fun': print_binary_and_numeric_options, 'arg': amenities_and_ad_filters}
    }

    accepted_selection = ['sort_by', 'property_type',
                          'property_size', 'kitchen_and_heating_type',
                          'amenities_and_ad_filters', 'print_all']
    selection = kwargs.get('selection')

    if selection not in accepted_selection:
        print_choice(selection_labels)
    elif selection == 'print_all':
        for k, v in selection_labels.items():
            print_options = v.get('fun')
            option = v.get('arg')
            print_options(option)
    else:
        try:
            print_type_options(eval(selection))
        except:
            print_binary_and_numeric_options(eval(selection))

        show_search_filters()
