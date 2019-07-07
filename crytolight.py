from configparser import ConfigParser
import urllib.request, json
import time

from phue import Bridge

"""
This code can be used to follow the BTC/USD(T) pairs with your Philips Hue lights.
In practice, with the current state of crypto, it will turn your living room into
a christmas tree or a techno club.

TODO
----
Keep light scenes as they are and just give a short notification of an increase
or drop.

"""

__author__ = "Robbin Bouwmeester"
__license__ = "Apache License, Version 2.0"
__version__ = "1.0"
__maintainer__ = "Robbin Bouwmeester"
__email__ = "Robbin.bouwmeester@ugent.be"


class CryptoLight():
    def __init__(self,
                 bridge_ip="192.168.0.254",
                 time_sleep=15,
                 from_curr=0,
                 to_curr=4,
                 past_from=4,
                 past_to=8,
                 store_max_prices=2,
                 flicker_lights=1,
                 transition_time=10,
                 flickr_amount=10,
                 max_diff=25.0,
                 max_bright=254,
                 base_url="https://min-api.cryptocompare.com/data/generateAvg?fsym=BTC&tsym=USD&e=",
                 exchanges=["Poloniex", "Kraken", "Coinbase"],
                 retries=100,
                 verbose=True):
        """
        __init__

        Parameters
        ----------
        bridge_ip : str
            provide the IP adress of your Hue bridge
        time_sleep : int
            amount of seconds to sleep between getting the new BTC price and setting new 
            colours/intensities for the lights
        from_curr : int
            index to start collecting prices that are considered 'new' or 'current' 
        to_curr : int
            index to stop collecting prices that are considered 'new' or 'current'
        past_from : int
            index to start collecting prices that are considered 'old' or 'past' 
        past_to : int
            index to stop collecting prices that are considered 'old' or 'past' 
        store_max_prices : int
            maximum number of prices to keep in memory
        max_diff : float
            maximum difference that will be used to set intensity and colour of the lights.
            In addition this value will be used for normalization of the difference between
            current and past prices.
        max_bright : float
            maximum brightness for the Hue light
        base_url : str
            base URL to collect the BTC/USD(T) pairs
        exchanges : list
            what exchanges to collect the BTC/USD(T) pairs
        retries : int
            number of retries for the exchange API
        verbose : boolean
            verbose?
        """
        self.bridge_ip = bridge_ip
        self.time_sleep = time_sleep
        self.from_curr = from_curr
        self.to_curr = to_curr
        self.past_from = past_from
        self.past_to = past_to
        self.base_url = base_url
        self.exchanges = exchanges
        self.retries = retries
        self.store_max_prices = store_max_prices
        self.flicker_lights = flicker_lights
        self.transition_time = transition_time,
        self.flickr_amount = flickr_amount,
        self.max_diff = max_diff
        self.max_bright = max_bright
        self.verbose = verbose

        if self.verbose:
            print("Trying to connect to the following bridge IP: %s" % (self.bridge_ip))
        self.b = Bridge(self.bridge_ip)
        self.b.connect()
        self.lights = self.b.lights
        if self.verbose:
            print("Found the following lights: %s" % (self.lights))
        self.prices = []

    def __str__(self):
        return """
                        _        _ _       _     _   
                       | |      | (_)     | |   | |  
   ___ _ __ _   _ _ __ | |_ ___ | |_  __ _| |__ | |_ 
  / __| '__| | | | '_ \| __/ _ \| | |/ _` | '_ \| __|
 | (__| |  | |_| | |_) | || (_) | | | (_| | | | | |_ 
  \___|_|   \__, | .__/ \__\___/|_|_|\__, |_| |_|\__|
             __/ | |                  __/ |          
            |___/|_|                 |___/           

       ,
     0/
    /7,
  .'(
'^ / >
  / < 
  `
              """

    def get_col(self,
                avg_curr_price,
                avg_past_price):
        """
        Return what the color of the lights should be (red or green) based on
        the current and previous price.

        Parameters
        ----------
        avg_curr_price : float
            current price
        avg_past_price : float
            past price

        Returns
        -------
        list
            list with two values indicating x,y positions of the color wheel
        """
        # Positive -> green
        if (avg_curr_price - avg_past_price) > 0.0:
            return([0.17, 0.7])
        # Negative -> red
        else:
            return([0.6744, 0.3212])

    def get_intensity(self,
                      avg_curr_price,
                      avg_past_price):
        """
        Return what the intensity of the lights should be (continuous) based
        on the current and previous price.

        Parameters
        ----------
        avg_curr_price : float
            current price
        avg_past_price : float
            past price
            
        Returns
        -------
        float
            float value for the intensity
        """
        # Calculate the relative difference over max difference and make it an integer (required)
        diff = abs(avg_curr_price - avg_past_price)
        rel_diff = diff/self.max_diff
        intensity = int(self.max_bright*rel_diff)

        # More than max brightness?
        if intensity > self.max_bright:
            intensity = self.max_bright

        return intensity

    def change_col_intensity(self,
                            bridge,
                            lights,
                            col,
                            intensity,
                            transition_time=10,
                            flicker_lights=1,
                            flickr_amount=5):
        """
        Deliver the payload to the lights function.

        Parameters
        ----------
        bridge : object
            current price
        lights : list
            past price
        col : list
            list of two values that define the x,y coordinates of the colour wheel
        intensity : int
            intensity value to set the lights
        transition_time : int
            time to flickr and transition to the new brightness/colour
        flicker_lights : boolean
            should the lights flicker?
        flickr_amount : int
            how many times should the lights flicker?
        """
        if self.flicker_lights == 1:
                curr_settings = bridge.get_light(lights[0].name)
                if col != curr_settings["state"]["xy"]:
                    for i in range(flickr_amount):
                        bridge.set_light([l.name for l in lights],{"on": False,
                                                                    "bri": intensity,
                                                                    "transitiontime": 1,
                                                                    "xy": col})
                        time.sleep(0.5)
                        bridge.set_light([l.name for l in lights],{"on": True,
                                                                    "bri": intensity,
                                                                    "transitiontime": 1,
                                                                    "xy": col})

        for l in lights:
            bridge.set_light(l.name, {"on": True,
                                        "bri": intensity, 
                                        "transitiontime": transition_time,
                                        "xy": col})

    def start_lights(self):
        """
        Start following the BTC/USD(T) price and change hue lights colours. This is the main function
        that needs to be called to start following... Does not start techno music to go with your
        lights.

        TODO - make stop_lights function
        """
        while True:
            time.sleep(self.time_sleep)
            # Get the pair prices
            self.prices.insert(0,get_curr_price(base_url=self.base_url,
                                                exchanges=self.exchanges,
                                                num_retries=self.retries,
                                                verbose=self.verbose))
            self.prices = self.prices[:self.past_to+self.store_max_prices]

            if self.verbose:
                print("Collected the following prices: %s" % (self.prices))

            if len(self.prices) < self.past_to+(self.store_max_prices-1):
                if self.verbose:
                    print("Skipping this time because we have not collected enough data yet (%s;%s)"
                           % (len(self.prices), 
                           self.past_to+(self.store_max_prices-1)))
                continue

            avg_curr_price = sum(self.prices[self.from_curr:self.to_curr])/len(self.prices[self.from_curr:self.to_curr])
            avg_past_price = sum(self.prices[self.past_from:self.past_to])/len(self.prices[self.past_from:self.past_to])

            change_col = self.get_col(avg_curr_price, avg_past_price)
            intensity = self.get_intensity(avg_curr_price, avg_past_price)

            #Deliver the payload to the lights
            self.change_col_intensity(self.b, self.lights, change_col, intensity)

            if self.verbose:
                print("Average current price: %s" % (avg_curr_price))
                print("Average past price: %s" % (avg_past_price))
                print("Changed color to: %s" % (change_col))
                print("Changed intensity to: %s" % (intensity))
                print("== Next iteration ==")

def get_curr_price(base_url="https://min-api.cryptocompare.com/data/generateAvg?fsym=BTC&tsym=USD&e=", 
                   exchanges=["Poloniex", "Kraken", "Coinbase"],
                   num_retries=100,
                   verbose=True):
    """
    Return what the intensity of the lights should be (continuous) based
    on the current and previous price.

    Parameters
    ----------
    base_url : str
        base URL for the API to get the price
    exchanges : list
        exchanges to get the price from
    num_retries : int
        how many retries if API call fails?
    verbose : boolean
        verbose function call?
        
    Returns
    -------
    float
        current price of BTC/USD(T) value
    """
    if len(exchanges) > 0:
        url_req = "%s%s" % (base_url, ",".join(exchanges))
    else:
        url_req = base_url

    retries = 0
    while retries < num_retries:
        retries += 1
        try:
            with urllib.request.urlopen(url_req) as url:
                data = json.loads(url.read().decode())
            curr_price = data["RAW"]["PRICE"]
        # TODO catch exact exception
        except:
            if verbose:
                print("Failed to get the current price at this number of retries: %s" % (retries))
            time.sleep(5)
            continue
        break
    if verbose:
        print("Current BTC/USD(T) pair price: %s" % (curr_price))
    return(curr_price)

if __name__ == "__main__":
    cparser = ConfigParser()
    cparser.read("cryptolight_config.ini")
    cl = CryptoLight(bridge_ip=cparser.get("general", "bridge_ip"),
                     time_sleep=cparser.getfloat("general", "time_sleep"),
                     from_curr=cparser.getint("general", "from_curr"),
                     to_curr=cparser.getint("general", "to_curr"),
                     past_from=cparser.getint("general", "past_from"),
                     past_to=cparser.getint("general", "past_to"),
                     retries=cparser.getint("general", "retries"),
                     flicker_lights=cparser.getint("general", "flicker_lights"),
                     transition_time=cparser.getint("general", "transition_time"),
                     flickr_amount=cparser.getint("general", "flickr_amount"),
                     store_max_prices=cparser.getint("general", "store_max_prices"),
                     max_diff=cparser.getfloat("general", "max_diff"),
                     max_bright=cparser.getfloat("general", "max_bright"))
    print(cl)
    cl.start_lights()