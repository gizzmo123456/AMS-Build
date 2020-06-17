import threading
import baseHTTPServer
from urllib.parse import urlparse, parse_qsl


class WebInterface( baseHTTPServer.BaseServer ):

    def init( self ):
        self.thr_lock_update_tasks = threading.Lock()
        self.active_builds = ""
        self.queued_tasks = ""

    def do_GET( self ):

        request = urlparse( self.path ).split("/")  # {root} / {project name} / {build name}
        path = request.path
        query = parse_qsl( request.query )

        if len(request) == 0 or request[1].lower() != "projects":
            self.process_request( "Im, lost!", 404, False )
        else:
            page_content = {
                "queue_text": "",
                "projects": "",
                "builds": "",
            }

            self.process_request( "Helloo World", 200, False )

    def update_tasks( self, active_tasks, queued_tasks ):
        """ Updates the tasks string,
            This should be called from the same thread that is using the list

        :param active_tasks:    list of active tasks
        :param queued_tasks:    list of queued tasks
        :return:
        """

        if len(active_tasks) == 0:
            active_tasks_str = "None"
        else:
            active_tasks_str = '<br />'.join( [ "{project} - {build_hash} - created @ {created} - By {actor}".format( **task[1].format_values ) for task in active_tasks ] )

        if len(queued_tasks) == 0:
            queued_tasks_str = "None"
        else:
            queued_tasks_str = '<br />'.join( [ "{project} - {build_hash} - created @ {created} - By {actor}".format( **task.format_values ) for task in queued_tasks ] )

        self.thr_lock_update_tasks.acquire()
        self.active_builds = active_tasks_str
        self.queued_tasks = queued_tasks_str
        self.thr_lock_update_tasks.release()

