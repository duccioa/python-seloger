# python-seloger
=================

A simple `SeLoger <http://www.seloger.com>`__ wrapper, based on the `python-craigslist <https://github.com/juliomalegria/python-craigslist>` scraper.

License: `MIT-Zero <https://romanrm.net/mit-zero>`__.

Disclaimer
----------

* I don't work for or have any affiliation with Seloger.
* This module was implemented for educational purposes. It should not be used for crawling or downloading data from Seloger.

Installation
------------
With git installed:

```shell
pip install git+https://github.com/duccioa/python-seloger

```
Depending on your system, you might have to use:
```shell
sudo -H pip3 install git+https://github.com/duccioa/python-seloger
```
Otherwise, try:

```shell
pip install --upgrade https://github.com/duccioa/python-seloger/master
```   

Classes
-------

Base class:

* ``SelogerBase``

Subclasses:

* ``SelogerAchat`` (seloger.com > Buy)
* ``SelogerLocation`` (seloger.com > Rent)
* ``SelogerLocationTemporaire`` (seloger.com > Short Rent)
* ``SelogerLocationViager`` (seloger.com > Viager sales)
* ``SelogerLocationInvestissement`` (seloger.com > Investment products)
* ``SelogerLocationVacances`` (seloger.com > Holiday rent)
* ``SelogerBiensVendus`` (seloger.com > Sold properties)

Every subclass links to the relevant search option. 

Filters
-----
Search filters have to be included in the form of a dictionary:
```python
search_filters = {
    'url_key1': 'value1',
    'url_key2': 'value2'
    }
```
``url_key`` is the API key for the search option (ex. 'tri' is the URL key for sorting) and ``value`` is the required values ('d_dt_crea' is the value for sorting by date).

To get a list of the URL keys, use the ``.show_search_options()`` class-method:

```python
from SeLoger import show_search_filters

show_search_filters() # to prompt a selection

show_search_filters(selection="print_all") # to show all the filters
```
 
Examples
--------

Let's find a 1 bedroom apartment for buying in the 15th Arrondissement of Paris, minimum 40 sqm and with a balcony at a maximum price of 500 000 euros.

```python
from SeLoger import SeLogerAchat

search_criteria = {'cp': '75015', 'idtypebien': '1', 'pxmax': '500000', 'surfacemin': '40','tri': 'd_dt_crea', 'nb_balconsmin': '1'}

rent_paris = SeLogerAchat(search_criteria)
results = rent_paris.get_results(2, print_results=1)
ads = []
for result in results:
    ads.append(result)

```

Looking for an office in Marseille? Let's save the results as a Pandas dataframe.

```python
from SeLoger import SeLogerLocation

search_criteria = {'cp': '33', 'idtypebien': '8', 'pxmax': '2000', 'surfacemin': '40', 'tri': 'd_dt_crea'}

office_marseille = SeLogerLocation(search_criteria, delay=5)
df = office_marseille.results_to_dataframe(4)
```
Future developments
-------
* Add log function
* Add error handling

Support
-------

If you find any bug or you want to propose a new feature, please use the `issues tracker <https://github.com/duccioa/python-seloger/issues>`__. I'll be happy to help you! :-)
