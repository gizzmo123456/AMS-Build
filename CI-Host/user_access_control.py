import user_manager
import commonProject
import time
import common
import const
import os

import DEBUG
_print = DEBUG.LOGS.print

class UAC:

    NO_AUTH         = 0             # No permissions
    USER            = 1             # View/download assigned project only
    WEBHOOK         = 2             # Triggers builds, if actor is listed in pipeline webhook config.
    TRIGGER         = 2             # Triggers jobs. (TODO: this is to replace WEBHOOK)
    MOD             = 3             # UAC_USER + Can trigger builds
    PROJECT_ADMIN   = 4             # UAC_MOD + Can Add/Assigned new user to project                (TODO)
    SERVER_ADMIN    = 5             # All permissions on all projects. # Can also add new projects  (TODO)

    __PROJECT_CACHE_TTL = 30        # seconds, update projects list, at most once every TTL

    def __init__(self, username=None, origin=None ):

        self.username = username            # the username the uac belogs to
        self.origin = origin                # The origin of witch the uac was created.

        self.access_level = UAC.NO_AUTH     # the users access level.

        self.projects = []  # this list of projects available to the user
        self.webhook  = None                # data required to authorize a webhook

        self.next_projects_update = 0

        # update the user if we have not originated from a webhook
        # otherwise wait for set_webhook to be called.
        if origin != "webhook":
            self.__update_user()

    def set_user( self, username, access_level ):

        self.username = username
        self.access_level = access_level

    def set_webhook(self, project, name, actor, branch, repo):

        if self.origin != "webhook":
            _print("UAC: Can not set webhook data on UAC that has not originated from 'webhook'")
            return

        self.webhook = {
            "project": project,
            "name": name,
            "actor": actor,
            "branch": branch,
            "repo": repo
        }

        # reset the projects next update time to make sure it updates now
        self.next_projects_update = 0
        self.__update_user( project )

    def compare_webhook_data(self, name, branch, repo):

        if self.origin != "webhook":
            return False

        # make sure the webhook data has been set correctly.
        for wh_key in self.webhook:
            if self.webhook[wh_key] is None:
                return False

        # don't compare the actor. since its possible the actor is being verified.
        return self.webhook["name"] == name and self.webhook["branch"] == branch and self.webhook["repo"] == repo

    def __update_user(self, project=None):

        if time.time() < self.next_projects_update:
            return

        self.next_projects_update = time.time() + UAC.__PROJECT_CACHE_TTL

        if self.origin == "webhook" and project is not None and self.__webhook_has_project_access( project ):
            self.projects = [project]
            self.access_level = UAC.TRIGGER
        elif self.origin != "webhook":
            user = user_manager.UserManager().get_user( self.username )

            if user is not None and "projects" in user and "access_level" in user:
                self.projects = user["projects"]
                self.access_level = user["access_level"] # TODO: make sure the access level exist.
            else:
                self.projects = []
                self.access_level = UAC.NO_AUTH
        else:
            self.projects = []
            self.access_level = UAC.NO_AUTH

    def has_project_access( self, project ):
        """ the in_webhooks must be supplied for webhook access """

        if self.access_level == UAC.NO_AUTH:
            return False

        self.__update_user()

        if self.origin == "webhook" and self.access_level == UAC.TRIGGER:
            return self.__webhook_has_project_access( project )
        elif self.origin != "webhook":
            return project in self.projects
        else:
            _print("UAC: Unable to get project access. Incorrect access level for webhook", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)

        return False

    def __webhook_has_project_access( self, project ):

        if self.access_level != self.TRIGGER or self.origin != "webhook":
            _print("uac does not originate from a webhook")
            return False
        elif self.webhook is None:
            _print("Unable to verify if webhook has project access. Webhook data not set in UAC")
            return False

        config_path = "{relevent_proj_path}/{project_name}/master/config/webhooks.json".format(
                        relevent_proj_path=const.RELEVENT_PROJECT_PATH,
                        project_name=project )

        if not os.path.exists( config_path ):
            _print("Unable to verify if webhook has project access. 'webhooks.json' does not exist")
            return False

        webhook_config = common.get_dict_from_json( config_path )

        if webhook_config is None:
            _print(f"Unable to load webhook config fro project {project}.")
            return False
        elif "in-webhooks" not in webhook_config:
            _print(f"No inbound webhooks configured for project '{project}'.")
            return False

        all_in_hooks = webhook_config.get( "in-webhooks", [] )

        for hook in all_in_hooks:
            if self.compare_webhook_data( hook.get( "name", None ), hook.get( "branch", None ), hook.get( "repository", None ) ):
                authorized_actors = hook.get( "authorized-actors", [] )
                return self.username in authorized_actors

        _print("Webhook not found.")

        return False

    def has_build_access( self, access_level ):
        return access_level > UAC.USER

    def is_valid( self ):
        return self.username is not None

    def has_uac_auth( self ):
        return self.is_valid() and self.access_level > UAC.NO_AUTH
