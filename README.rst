SeLoger wrapper
---------------
Example::

    >>> from SeLoger import SeLogerAchat

    >>> search_criteria = {'cp': '75015', 'idtypebien': '1', 'pxmax': '500000', 'surfacemin': '40','tri': 'd_dt_crea', 'nb_balconsmin': '1'}

    >>> rent_paris = SeLogerAchat(search_criteria)
    >>> results = rent_paris.get_results(2, print_results=1)
    >>> ads = []
    >>> for result in results:
    >>>     ads.append(result)

