import user_manager
import commonProject
import time
import common

import DEBUG
_print = DEBUG.LOGS.print

class UAC:

    NO_AUTH         = 0             # No permissions
    USER            = 1             # View/download assigned project only
    WEBHOOK         = 2             # Triggers builds, if actor is listed in pipeline webhook config.
    MOD             = 3             # UAC_USER + Can trigger builds
    PROJECT_ADMIN   = 4             # UAC_MOD + Can Add/Assigned new user to project                (TODO)
    SERVER_ADMIN    = 5             # All permissions on all projects. # Can also add new projects  (TODO)

    __PROJECT_CACHE_TTL = 30        # seconds, update projects list, at most once every TTL

    def __init__(self, username=None, access_level=NO_AUTH, subname=None):

        self.username = username            # the user the uac belogs to
        self.subname = subname              # the subname is used to store any secondary names. ie the webhook name.
        self.access_level = access_level    # the users access level

        self.projects = []                  # this list of projects available to the user, does not apply to webhooks
        self.next_projects_update = 0


    def set_user( self, username, access_level ):

        self.username = username
        self.access_level = access_level

    def __update_user_projects( self ):

        if time.time() < self.next_projects_update:
            return

        self.next_projects_update = time.time() + UAC.__PROJECT_CACHE_TTL

        if self.access_level == UAC.NO_AUTH or self.access_level == UAC.WEBHOOK:
            self.projects = []
            return

        user = user_manager.UserManager().get_user( self.username )

        if user is not None and "projects" in user and user["projects"] is not None:
            self.projects = user[ "projects" ]
        else:
            self.projects = []

    def has_project_access( self, project, webhooks=None ):
        """ the in_webhooks must be supplied for webhook access """

        if self.access_level == UAC.NO_AUTH:
            return False

        self.__update_user_projects()

        if webhooks is not None and "in-webhooks" in webhooks and self.access_level == UAC.WEBHOOK:
            all_in_hooks = common.get_value_at_key( webhooks, "in-webhooks", noValue=[] )
            for wh in all_in_hooks:
                if common.get_value_at_key(wh, "name", noValue="") == self.subname:
                    authorized_actors = common.get_value_at_key( wh, "authorized-actors", noValue=[] )
                    if self.username in authorized_actors:
                        return True
                    else:
                        return False    # actor not in webhook actor list
            return False    # webhook not found
        elif self.access_level != UAC.WEBHOOK:
            return project in self.projects

        return False

    def has_build_access( self, access_level ):
        return access_level > UAC.USER

    def is_valid( self ):
        return self.username is not None

    def has_uac_auth( self ):
        return self.is_valid() and self.access_level > UAC.NO_AUTH
