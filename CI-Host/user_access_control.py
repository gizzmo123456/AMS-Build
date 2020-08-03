import user_manager

class UAC:

    NO_AUTH         = 0             # No permissions
    USER            = 1             # View/download assigned project only
    WEBHOOK         = 2             # Triggers builds if actor, is listed in webhook config.
    MOD             = 3             # UAC_USER + Can trigger builds
    PROJECT_ADMIN   = 4             # UAC_MOD + Can Add/Assigned new user to project                (TODO)
    SERVER_ADMIN    = 5             # All permissions on all projects. # Can also add new projects  (TODO)

    def __init__(self, username=None, access_level=NO_AUTH):

        self.username = username            # the user the uac belogs to
        self.access_level = access_level    # the users access level
        self.projects = []                  # this list of projects available to the user, does not apply to webhooks

    def set_user( self, username, access_level ):

        self.username = username
        self.access_level = access_level

    def update_user_projects( self, username ):

        if self.access_level == UAC.NO_AUTH or self.access_level == UAC.WEBHOOK:
            self.projects = []
            return

        user = user_manager.UserManager().get_user( username )

        if user is not None:
            self.projects = user[ "projects" ]
        else:
            self.projects = []

    def has_build_access( self, access_level ):

        return access_level > UAC.USER

    def is_valid( self ):
        return self.username is not None

    def has_uac_auth( self ):
        return self.is_valid() and self.access_level > UAC.NO_AUTH
