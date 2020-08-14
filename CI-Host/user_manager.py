import common
import commonProject
import cipher
import os
import string
import random
import DEBUG
_print = DEBUG.LOGS.print


class UserManager:

    USER_SECRET_MIN_LEN = 6
    DEFAULT_USER_PASSWORD_LEN = 6

    def __init__( self ):

        self.users_path = "./data/users.json"
        self.path = "./data/.secrets/"
        self.hasher = cipher.Hash( self.path, "users" )

        self.create_user_data()

    def create_user_data(self):
        """ Creates the user files, if they don't already exist """

        default_accounts = [{
            "username": "admin",        # This account should be treated as a honeytoken
            "secret": UserManager.create_random_secret(),
            "projects": None,           # Hide all projects on honeytoken account
            "access_level": 1           # Give lowest access level
        }]

        created = common.get_or_create_json_file("./data", "users.json", default_accounts)[0]

        if created:
            user_secret = self.create_random_secret( UserManager.DEFAULT_USER_PASSWORD_LEN )
            self.__update_secret( default_accounts[0]["secret"], user_secret )
            _print("User files created!")
            _print("Test Account")
            _print("\tUsername: ", default_accounts[0]["username"] )
            _print("\tPassword: ", user_secret )
            _print("To add or update a user, run user manager in standalone mode")

    @staticmethod
    def create_random_secret( len=64 ):
        chars = (string.ascii_letters + string.digits)*3 + string.punctuation
        return ''.join(random.choice( chars ) for _ in range(len))

    def __update_secret( self, secret_one, secret_two):

        lines = []

        if os.path.exists( self.path + "users" ):
            with common.LockFile( self.path + "users", "r" ) as file:
                lines = file.readlines()

        # hash the 2 secrets
        self.hasher.new()       # we must get a new hasher, as it hashes in block.
        secret_one = self.hasher.digest( secret_one )
        secret_two = self.hasher.digest( secret_two )

        write_mode = None
        data = None

        for i in range( len(lines) ):
            secrets = lines[i].split( " " )
            if secrets[0] == secret_one:
                # update secrets file
                secrets[1] = secret_two+"\n"
                lines[i] = ' '.join( secrets )

                write_mode = 'w'
                data = ''.join( lines )
                break

        # append the new secret
        if write_mode is None:
            write_mode = 'a'
            data = "\n{0} {1}".format(secret_one, secret_two)

        if data[-1:] == "\n":
            data = data[:-1]

        with common.LockFile( self.path + "/users", write_mode ) as file:
            file.write( data )

    def __authorize_secret( self, secret_one, secret_two ):

        if not os.path.exists( self.path + "users" ):
            return False

        with common.LockFile( self.path + "users", "r" ) as file:
            secrets = file.readlines()

        # hash the 2 secrets
        self.hasher.new()       # we must get a new hasher, as it hashes in block.
        secret_one = self.hasher.digest( secret_one )
        secret_two = self.hasher.digest( secret_two )

        for s in secrets:
            if s[-1] == "\n":
                s = s[:-1]
            if "{0} {1}".format( secret_one, secret_two) == s:
                return True

        return False

    def get_users( self ):
        return common.get_dict_from_json( self.users_path, True )

    def get_user( self, username ):
        users = self.get_users()

        for u in users:
            if u[ "username" ].lower() == username.lower():
                return u

        return None

    def user_exist(self, username):
        return self.get_user( username ) is not None

    def add_user(self, username, secret, projects=None, access_level=1):

        if len(secret) < UserManager.USER_SECRET_MIN_LEN:
            return False

        users = self.get_users()

        account = {
            "username": username,
            "secret": UserManager.create_random_secret(),
            "projects": projects,
            "access_level": access_level
        }

        users.append( account )

        self.__update_secret( account["secret"], secret )

        common.create_json_file( self.users_path, users )
        return True

    def update_user_secret( self, username, secret ):

        if len(secret) < UserManager.USER_SECRET_MIN_LEN:
            return False

        users = self.get_users()

        for user in users:
            if user["username"] == username:
                self.__update_secret( user["secret"], secret )
                return True

        return False

    '''
    def remove_user(username, secret):
        pass
    '''

    def authorize_user(self, username, secret):
        """ Authorizes user returning the users access
            :return: UAC
        """

        #TODO: return UAC object

        user = self.get_user( username )

        if user is not None and self.__authorize_secret( user["secret"], secret ):
            return user["access_level"]
        else:
            return 0    # NO ACCESS # TODO: move UAC's in WWWUser to its own thing


if __name__ == "__main__":
    # if ran as a standalone, takes a username and file containing the secret to encrypt
    user_man = UserManager()

    while True:
        # Add user.
        print("Enter Username")
        add_username = input()
        add_projects = []
        add_access_level = 0

        user_exist = user_man.user_exist( add_username )
        successful = False

        if user_exist:
            print( "User already exist" )
            print( "To update the users password supply the old password on line 1 and new new on line 2" )

        print("Enter Project Names that the user has access to (case sensitive)")
        print("leave input empty to continue")
        proj = " "
        while proj != "":
            proj = input()
            exist = commonProject.__project_exist( proj )
            if proj != "" and exist:
                add_projects.append( proj )
                print("Project Added! Enter another project or hit return to continue.")
            elif not exist:
                print("Project does not exist!")


        print("Enter the users access level ID (INT)")
        print("1 - User (project api, download, output file) (min access)")
        print("3 - Moderator")
        print("4 - Admin")
        print("5 - Server Admin (All Access) (max access)")
        ac_levels = [1, 3, 4, 5]
        while add_access_level not in ac_levels: # <1=noAccess, 2=webhook, 5=serverAdmin, >5 not defined
            try:
                add_access_level = int(input())
            except:
                pass
            if add_access_level not in ac_levels:
                print("Invalid input, please enter 1, 3, 4 or 5")

        print("Enter path to password file (leave empty to use ./data/new_user), or N to exit, C to start again")
        print("password must have a min length of", UserManager.USER_SECRET_MIN_LEN )

        add_pass_file = input()

        if len(add_pass_file) == 0:
            add_pass_file = "./data/new_user"

        if add_pass_file.lower() == 'n':
            exit()
        if add_pass_file.lower() == 'c':
            continue

        try:
            with open( add_pass_file, mode='r') as file:
                lines = file.readlines()
        except Exception as e:
            print("Failed to open file,", e)
            continue

        if not user_exist and len(lines) > 0 and len(lines[0]) >= UserManager.USER_SECRET_MIN_LEN:
            # remove new line chars
            lines[0] = lines[0].replace('\n', "").replace('\r', "")

            successful = user_man.add_user( add_username, lines[0], add_projects, add_access_level )
            print( "User Added? ", successful )
        elif user_exist and len( lines ) > 1 and len( lines[1] ) >= UserManager.USER_SECRET_MIN_LEN:
            # remove new line chars
            lines[0] = lines[0].replace('\n', "").replace('\r', "")
            lines[1] = lines[1].replace('\n', "").replace('\r', "")
            # auth user
            if user_man.authorize_user( add_username, lines[0] ):
                successful = user_man.update_user_secret( add_username, lines[1])
                print("Password updated? ", successful)
            else:
                print("User Auth Failed")
        else:
            print("Error: Either the password is to short; or")
            print("if updating, both new and old passwords are not supplied")
            print("or old password is incorrect or new password is to short")

        if successful:
            with open( add_pass_file, mode='w' ) as file:
                file.write( "." )  # overwrite the passwords

        print("Add another user? (y/n)")
        cont = None

        while cont != 'y' and cont != 'n':
            cont = input().lower()

            if cont == 'n':
                exit()
            elif not 'y':
                print("Invalid input")
                print( "Add another user? (y/n)" )
