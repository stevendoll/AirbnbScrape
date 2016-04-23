import requests
import bs4
import json
from time import sleep
from random import randint
import csv

def parse_main_page(location='Cambridge--MA', pages=1):

    base_url = 'https://www.airbnb.com/s/'
    page_url = '?page='
    headers = {'User-agent':'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'}
    
    main_results = []


    try:
        for n in range(1, pages+1):

            #random time delay for scraping
            sleep(randint(0,2))

            url = ''.join([base_url, location, page_url, str(n)])

            print('Processing main page %s of %s %s' % (str(n), str(pages), url))
                        
            r = requests.get(url, headers=headers)
            #print(r.status_code)
            
            # get listing information from div
            soup = bs4.BeautifulSoup(r.text, "lxml")
            listings = soup.find_all("div", {"class" : "listing"})
            
            # iterate through listing data on main page
            for listing in listings:
                _dat = {}
                _dat['index_url'] = url
                _dat['page'] = n
                _dat['lat'] = float(listing['data-lat'])
                _dat['long'] = float(listing['data-lng'])
                _dat['id'] = int(listing['data-id'])
                _dat['name'] = listing['data-name']
                _dat['price'] = int(listing['data-price'].replace('<sup>$</sup>', '').replace('<sup></sup>', ''))
                _dat['review_count'] = int(listing['data-review-count'])
                _dat['star_rating'] = float(listing['data-star-rating'])
                _dat['listing_url'] = listing['data-url']
                _dat['user'] = int(listing['data-user'])
                
                #check boolean params and convert to boolean
                if listing['data-instant-book'] == 'true':
                    _dat['instant_book'] = True
                else:
                    _dat['instant_book'] = False
                        
                if listing['data-has-new-listing-badge'] == 'true':
                    _dat['new_listing_badge'] = True
                else:
                    _dat['new_listing_badge'] = False

                if listing['data-has-superhost-badge'] == 'true':
                    _dat['superhost_badge'] = True
                else:
                    _dat['superhost_badge'] = False
                                
                # get additional information from listing page
                _dat = parse_listing_page(_dat)

                main_results.append(_dat)
            
    except:
        print('This page did not return results: %s ' % url)

    print('Done processing main page')
    return main_results

def parse_listing_page(_dat):
    
    listing_base_url = 'https://www.airbnb.com'
    headers = {'User-agent':'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'}

    try:
        
        #random time delay for scraping
        sleep(randint(0,2))

        url = ''.join([listing_base_url, _dat['listing_url']])
        print('Processing listing page %s' % url)

        r = requests.get(url, headers=headers)
        #print(r.status_code)

        soup = bs4.BeautifulSoup(r.text, "lxml")
        
        parsed = json.loads(soup.find("script", {"data-mystique-key" : "listingbundlejs"}).text.replace('<!--','').replace('-->',''))

        #amenities
        try:
            for amenities in parsed['listing']['listing_amenities']:
                if amenities['is_present'] == True:
                    _name = amenities['name'].replace(' ', '_').replace('-', '_').replace('/', '_').lower()
                    _dat[_name] = True
                else:
                    _dat[_name] = False
        except:
            print('Failed getting amenities: %s' % url)
        
        #host
        try:
            _dat['about_host'] = parsed['aboutTheHost']['host_details']['about']
            _dat['member_since'] = parsed['aboutTheHost']['host_details']['member_since']
            _dat['response_rate'] = parsed['aboutTheHost']['host_details']['response_rate']['rate']
            _dat['response_time'] = parsed['aboutTheHost']['host_details']['response_time']
            _dat['host_name'] = parsed['aboutTheHost']['host_details']['user']['host_name']
        except:
            print('Failed getting host information: %s' % url)

        
        try:
            _dat['listing_description'] = parsed['listing']['description'] 
            _dat['cancellation_policy_category'] = parsed['listing']['cancellation_policy_category'] 
            _dat['listing_house_rules'] = parsed['listing']['house_rules'] 
        except:
            print('Failed getting description: %s' % url)


        try:
            _dat['localized_minimum_nights_description'] = parsed['listing']['localized_minimum_nights_description'] 
            _dat['localized_description'] = parsed['listing']['localized_description'] 
        except:
            print('Failed getting localized info: %s' % url)


        try:
            _dat['localized_sectioned_access'] = parsed['listing']['localized_sectioned_description']['access']
            _dat['localized_sectioned_description'] = parsed['listing']['localized_sectioned_description']['description']
            _dat['house_rules'] = parsed['listing']['localized_sectioned_description']['house_rules']
            _dat['interaction'] = parsed['listing']['localized_sectioned_description']['interaction']
            _dat['localized_name'] = parsed['listing']['localized_sectioned_description']['name']
            _dat['neighborhood_overview'] = parsed['listing']['localized_sectioned_description']['neighborhood_overview']
            _dat['notes'] = parsed['listing']['localized_sectioned_description']['notes']
            _dat['space'] = parsed['listing']['localized_sectioned_description']['space']
            _dat['summary'] = parsed['listing']['localized_sectioned_description']['summary']
            _dat['transit'] = parsed['listing']['localized_sectioned_description']['transit']
        except:
            print('Failed getting localized sectioned info: %s' % url)

        try:
            _dat['min_nights'] = parsed['listing']['min_nights']
            _dat['name'] = parsed['listing']['name']
            _dat['person_capacity'] = parsed['listing']['person_capacity']
        except:
            print('Failed min nights and capacity: %s' % url)


        # loop through keys in price interface because some are empty
        for cur in ['cancellation_policy', 'cleaning_fee', 'extra_people', 'monthly_discount', 'monthly_price', 'permit', 'security_deposit', 'weekly_price', 'weekly_discount']:

            if parsed['listing']['price_interface'][cur]:
                _dat[cur] = parsed['listing']['price_interface'][cur]['value']
            else:
                _dat[cur] = 0
                print('  No %s: %s' % (cur, url))                   

    except:
        print('Error getting listing details for: %s' % url)
    
    return _dat


if __name__ == '__main__':

    location = 'Washington--D%252EC%252E--DC--United-States'
    
    #get results
    listings = parse_main_page(location=location, pages=5)

    #create filename
    filename = location.replace('--', '_').replace('-', '_').lower() + '.csv'
    
    #get all keys
    headings = sorted(list(set().union(*(d.keys() for d in listings))))
    
    #write to csv file
    with open(filename, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, headings)
        dict_writer.writeheader()
        dict_writer.writerows(listings)