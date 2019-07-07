# cryptolight

Change the colour and intensity of your hue lights based on bitcoin / US dollar prices (BTC/USD(T)).

To run the script:

1. Install the environment from the .yml file
2. Change the IP in the cryptolight_config.ini file to your hub
3. Run the crytolight.py script

## Parameters

Following parameters can be changed in the configuration file:

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
