
var refreshRate = 20;   //seconds

var loadContent = function(url, responceElem){

    var request = new XMLHttpRequest();
            request.onreadystatechange = function()
            {
                if (this.readyState == 4 && this.status == 200)
                {
                    responceElem.innerHTML = this.responseText;
                }
                else if ( this.status >= 300)
                {
                    responceElem.innerHTML = ` Error: ${this.status}`
                }
            };

            request.open("GET", url, true);
            request.send();

}

var updateActiveTask = function(){
    loadContent( "/ams-ci/api/tasks/active?template=active_task", "items-active-tasks" )
}

var updateQueuedTask = function(){
    loadContent( "/ams-ci/api/tasks/queued?template=queued_task" "items-queued-tasks" )
}

var updateProjects = function(){
    loadContent( "/ams-ci/api/projects?template=project", "items-queued-tasks" )
}

var updateBuilds = function( selected ){
    loadContent( `/ams-ci/api/projects/${selected}/builds?template=builds`, "items-queued-tasks" )
}

setInterval( updateActiveTask, refreshRate );
setInterval( updateQueuedTask, refreshRate );