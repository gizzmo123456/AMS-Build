import urllib.parse
import urllib.request
import json
import DEBUG

_print = DEBUG.LOGS.print


class BaseOutWebhook:

    def __init__( self, webhook_url ):

        self.webhook_url = webhook_url
        self.default_data_fields = {}         # set default data so it cant be missed when making a request # Also this needs overriding
        self.headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}

    def get_main_data( self, **data ):
        return { **self.default_data_fields, **data }

    def _send_request( self, **data ):

        out_data = json.dumps( data )  # override the default data with the new data

        post_data = urllib.parse.urlparse( out_data )
        post_data = post_data.encode( 'ascii' )

        # set the length of the post data
        self.headers["Content-length"] = str( len(out_data) )

        request = urllib.request.Request( self.webhook_url, post_data, self.headers )

        with urllib.request.urlopen( request ) as response:
            page = response.read()

    @staticmethod
    def format_webhook_data(data, format_data):
        """Formats every string value in a nested list/dict combo :)"""
        if type( data ) is list:
            keys = range( len(data) )
        elif type(data) is dict:
            keys = data
        elif type( data ) is str:
            return BaseOutWebhook.format_string( data, format_data )
        else:
            return data

        for k in keys:
            if type( data[k] ) is list or type( data[k] ) is dict:
                data[k] = BaseOutWebhook.format_webhook_data( data[k], format_data)
            elif type( data[k] ) is str:
                data[k] = BaseOutWebhook.format_string( data[k], format_data )
            # we dont need to worry about over values

        return data

    @staticmethod
    def format_string( string, format_values ):
        """Make sure that no keys error are thrown when formatting"""
        formatted = False

        while not formatted:
            try:
                return string.format( **format_values )
                formatted = True
            except KeyError as e: # add the key and try again :)
                _print("KeyError:", str(e), "-> Adding key with value of key", print_now=True)
                format_values[str(e)[1:-1]] = str(e)[1:-1]
            except Exception as e: # We can only handle key errors, so we must exit
                raise e

    def execute_json( self, webhook_def_data_dict, format_data ):
        """ Executes a out webhook definition defined in project/master/config/wenhook.json
            Requires overriding
        :param webhook_def_cont_dict:   The data dict defined in the webhook definition
        :param format_data:             the format string data available to the hook
        :return:                        None
        """
        pass

class DiscordsWebhook( BaseOutWebhook ):

    def __init__(self, webhook_url):
        # see https://gist.github.com/Birdie0/78ee79402a4301b1faf412ab5f1cdcf9 about discords webhooks
        super().__init__(webhook_url)

        self.default_data_fields = {
            "content": "Im A Webhook For Discords",
            "username": "AMS-Build Webhook Bot",
            "avatar_url": "https://i.imgur.com/4M34hi2.png"
        }

        self.embed = []

    def add_embed( self, title="\u200B", description="\u200B", **kargs ):   # we must use kargs as we use unpacking to input the param data

        self.embed.append({
            "title": title,
            "description": description,
            "color": 15258703
        })

    def add_embed_field( self, name="\u200B", value="\u200B", inline=True, **kargs ): # we must use kargs as we using unpacking
        """Adds field data to the last embed"""

        if len(self.embed) == 0:
            self.add_embed("", "")

        embed_id = len(self.embed) - 1
        if "fields" not in self.embed[embed_id]:
            self.embed[embed_id]["fields"] = []

        self.embed[embed_id]["fields"].append( {
            "name": name,
            "value": value,
            "inline": inline
        } )

    def execute_json( self, webhook_def_data_dict, format_data ):

        data_dict = BaseOutWebhook.format_webhook_data( webhook_def_data_dict, format_data )
        main_data = self.get_main_data( **data_dict["default"] )

        if "embeds" in data_dict:
            for e in data_dict["embeds"]:
                self.add_embed( **e )

                if "fields" in e:
                    for ef in e["fields"]:
                        self.add_embed_field( **ef )

        _print("EXE OUT:", data_dict, print_now=True)
        self._send_request( **main_data, embeds=self.embed )

        # reset the embeds and fields, in case of re-use.
        self.embed = [ ]
