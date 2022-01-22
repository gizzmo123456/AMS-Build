
# NOTE: this replaces user_access_control.py
import DEBUG

_print = DEBUG.LOGS.print

class UAC:
    """
    UAC is a representation of a user and there permission.
    The UAC obj does not grant permission to users.
    Permission must be authorized via the user manager.
    Permissions must be checked at regular intervals of witch is configured in the user manager.
    The UAC obj is only valid if not None and the token is registered in the user manager and no older than the expiry timestamp.

    """

    UAC_NO_AUTH = 0x0
    UAC_READ    = 0x1   # allows the user to read (view and download) the project
    UAC_WRITE   = 0x2   # allows the user to edit project configs
    UAC_EXECUTE = 0x4   # allows the user to execute tasks and actions
    UAC_TASK    = 0x8   # defines the token type. if not set, uses the user token otherwise uses the task token.
    # A user token expires after inactive period of time (as defined in user_manager)
    # While a task token is valid until executed.

    UAC_PERMISSION_CONVERT = [
        ("t", UAC_TASK),
        ("r", UAC_READ),
        ("w", UAC_WRITE),
        ("x", UAC_EXECUTE)
    ]

    UAC_PERMISSION_NOT_ASSIGNED = "-"

    # for ADMIN global permissions are the minimal permissions assigned to ALL projects
    # global permissions are not permitted for other user groups
    USER_GROUP_ADMIN  = "admin"
    USER_GROUP_USER   = "user"
    USER_GROUP_CLIENT = "client"
    USER_GROUP_HOOK   = "hook"

    ACCEPTED_USER_GROUPS = [
        USER_GROUP_ADMIN,
        USER_GROUP_USER,
        USER_GROUP_CLIENT,
        USER_GROUP_HOOK
    ]

    def __init__(self, username, display_name, token, project_permissions, user_group=USER_GROUP_USER, global_permissions="----"):
        """

        :param username:            the logged in users username
        :param display_name:        the logged in users display name or webhook name respectively
        :param token:               the user token assigned to this user on a valid login
                                    or a list of single use task tokens to be consumed at execution
        :param project_permissions: a dictanary containing the project name (key) and the permissions  ie.
                                    {"ExampleProject": "-rwx", "ExampleProject_2: "t--x"), ...}
                                    if the task (t) flag is present, the uac is verified using task authentication,
                                    otherwise if the t flag is not present the uac is verified using the user authentication.
        :param user_group:          The group that the user belongs to. the groups effect the way that permissions are handled
        :param global_permissions:  default = '----' no global permissions. the left hand char must always be '-'
        """

        # user
        self.__username = username
        self.__display_name = display_name
        self.__user_group = user_group

        # permissions
        self.__token = token
        self.__project_permissions = self.__convert_permissions( project_permissions )
        self.__global_permissions  = self.__convert_permission_string( global_permissions )

        self.__validate()

    @property
    def user_info( self ):
        return {
            "username": self.__username,
            "display_name": self.__display_name,
            "user_group": self.__user_group
        }

    def transfer_token_and_permissions( self, id ):
        """
            Transfers the UAC token and permission to the user manager, for authentication.
            In the case of a task token, the token is remove upon transfer
        :param id: the ID that the user manager will read the token and permissions from
        """
        # TODO: new user manager.
        pass

    def __convert_permissions(self, project_permissions):
        """
            Converts the permission string to permission level (int)
        :param permissions: list of projects and permissions to convert
        :return:
        """

        for project in project_permissions:

            if not self.is_valid:
                break

            project_permissions[ project ] = self.__convert_permission_string( project_permissions[ project ] )

        return project_permissions

    def __convert_permission_string(self, permission_string):

        if len(permission_string) != 4:
            _print("Unable to set users permissions. Incorrect permission string. must be 4 in length and formated as 'trwx' using '-' for no permission",
                   message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
            self.invalidate()
            return UAC.UAC_NO_AUTH

        permission = UAC.UAC_NO_AUTH

        for i in range(4):
            char, value = UAC.UAC_PERMISSION_CONVERT[i ]

            if permission_string[i] == char:
                permission += value
            elif permission_string[i] != UAC.UAC_PERMISSION_NOT_ASSIGNED:
                _print(f"Unable to set user permissions. Incorrect permission string at position {i+1}."
                       f" Expected: '{char}' or '{UAC.UAC_PERMISSION_NOT_ASSIGNED}' Got '{permission_string[i]}'")
                self.invalidate()
                return UAC.UAC_NO_AUTH

        return permission

    def has_project_access(self, project):
        return project in self.__project_permissions and self.__project_permissions[project] > UAC.UAC_NO_AUTH

    def __validate(self):
        # if any of the permissions are invalid the token is revoked (set to None)

        if self.__user_group not in UAC.ACCEPTED_USER_GROUPS:
            _print(f"Invalid user group assigned to UAC Object ({self.__user_group})")
            self.invalidate()
            return

        is_task = False
        assigned_project_count = len( self.__project_permissions )

        for project in self.__project_permissions:
            permission = self.__project_permissions[ project ]
            is_task = permission & UAC.UAC_TASK > 0

            if is_task and assigned_project_count > 1:
                _print(f"Invalid permission set for project (user: {self.__username} project: {project} is_task: {is_task}). "
                       f"Task flag set, with more than one project assigned.",
                       message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
                self.invalidate()
                return
            elif is_task and ( permission & UAC.UAC_READ or permission & UAC.UAC_WRITE ):
                _print(f"Invalid permission set. (user: {self.__username} project: {project} is_task: {is_task})"
                       f"Task flag set with read and/or write permission set. This is not permitted.")
                self.invalidate()
                return

        if (is_task and self.__global_permissions > UAC.UAC_NO_AUTH) or \
           (self.__user_group != UAC.USER_GROUP_ADMIN and self.__global_permissions > UAC.UAC_NO_AUTH):
            _print("Invalid permission set. Non-admin and tasks can not have global permission set.")
            self.invalidate()

    def invalidate(self):
        self.__token = None

    @property
    def is_valid(self):
        return self.__token is not None


if __name__ == "__main__":

    import time

    DEBUG.LOGS.init()



    tests = {
        "invalid_user_group": ( "valid_user", "valid display name", "valid-user-token", {"Example": "-rwx"}, "bobs user group" ),
        "valid_user" : ( "valid_user", "valid display name", "valid-user-token", {"Example": "-rwx"} ),
        "invalid_user_with_global": ( "invalid_user_with_global", "invalid display name", "valid-user-token", { "Example": "-rwx" }, UAC.USER_GROUP_USER, "---x" ),
        "invalid_user_with_task" : ( "invalid_user_with_task", "invalid display name", "valid-user-token", {"Example": "trwx"} ),
        "invalid_permissions": ( "invalid_permissions", "invalid display name", "valid-user-token", {"Example": "rwx"} ),
        "invalid_permissions2": ( "invalid_permissions2", "invalid display name", "valid-user-token", {"Example": "-twx"} ),
        "invalid_global_permission": ( "invalid_global_permission", "invalid display name", "valid-user-token", {"Example": "-rwx"}, UAC.USER_GROUP_ADMIN, "-rwe" ),
        "valid_task" : ( "valid_task", "Valid task name", "valid-task-token", {"Example": "t--x"}, UAC.USER_GROUP_HOOK ),
        "invalid_task_to_many_projects" : ( "invalid_task_to_many_projects", "Valid task name", "valid-task-token", {"Example": "t--x", "Invalid-Project": "t--x"}, UAC.USER_GROUP_HOOK  ),
        "invalid_task_with_global" : ("invalid_task_with_global", "Valid task name", "valid-task-token", {"Example": "t--x"}, UAC.USER_GROUP_HOOK, "t--x"),
    }

    for key in tests:
        p_strs = list( tests[key][3].values() )
        uac = UAC(*tests[key])
        _print( f"{key} is valid: {uac.is_valid}. permission_str: {p_strs} # code: {list(uac.__project_permissions.values())}" )
        _print("-- ** --")