import urllib.parse
import urllib.request
import json

class BaseOutWebhook:

    def __init__( self, webhook_url ):

        self.webhook_url = webhook_url
        self.default_data_fields = {}         # set default data so it cant be missed when making a request # Also this needs overriding
        self.headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}

    def send_request( self, **data ):

        out_data = json.dumps( {**self.default_data_fields, **data} )  # override the default data with the new data

        post_data = urllib.parse.urlparse( out_data )
        post_data = post_data.encode( 'ascii' )

        # set the length of the post data
        self.headers["Content-length"] = str( len(out_data) )
        print(out_data)

        request = urllib.request.Request( self.webhook_url, post_data, self.headers )

        with urllib.request.urlopen( request ) as response:
            page = response.read()

        print(page)


class DiscordsWebhook( BaseOutWebhook ):

    def __init__(self, webhook_url):
        # see https://gist.github.com/Birdie0/78ee79402a4301b1faf412ab5f1cdcf9 about discords webhooks
        super().__init__(webhook_url)

        self.default_data_fields = {
            "content": "Im A Webhook For Discords",
            "username": "AMS-CI Webhook Bot",
            "avatar_url": "https://i.imgur.com/4M34hi2.png"
        }

        self.embed = {
            "title": "",
            "description": "",
            "color": 15258703
        }

    def set_embed( self, title, description ):

        self.embed["title"] = title
        self.embed["description"] = description
        self.embed["description"] = description

    def add_embed_field( self, name, value, inline=True ):

        if "fields" not in self.embed:
            self.embed["fields"] = []

        self.embed["fields"].append( {
            "name": name,
            "value": value,
            "inline": inline
        } )

    def send_request( self, **data ):

        data["embeds"] = [self.embed]

        super().send_request( **data )

        self.set_embed( "", "" )

        if "fields" in self.embed:
            del self.embed["fields"]


if "__main__" == __name__:
    b = DiscordsWebhook("https://discord.com/api/webhooks/746203039496667207/Ybu1oAQeKCIrDPfp0pwZ-5b4nR9sun7PiAUsJ_9YbEdr6SWRKhxjRfAgi16cBjjaqI2U")
    b.set_embed("Helloo", "World :)")
    b.add_embed_field("f 1", "yep")
    b.add_embed_field("f 2", "yep")
    b.add_embed_field("f 3", "nop nop nop nop", False)
    b.send_request(content="hellooWorld")
