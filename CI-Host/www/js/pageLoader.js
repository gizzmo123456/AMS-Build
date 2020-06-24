
var refreshRate = 20;   //seconds

var loadContent = function(url, responseElemId){

    var request = new XMLHttpRequest();
        request.onreadystatechange = function()
        {
            console.log( `URL ${url} ||| Ready State ${this.readyState} ||| Status ${this.status}` )

            if (this.readyState == 4 && this.status == 200)
            {
                document.getElementById(responseElemId).innerHTML = this.responseText;
                console.log( url + 'Received Response: ' + this.responseText );
            }
            else if ( this.status >= 300)   // should this be a thing ??
            {
                document.getElementById(responseElemId).innerHTML = ` Error: ${this.status}`
            }
        };

        request.open("GET", url, true);
        request.send();
        console.log(` url ${url} sent `)

}

var updateActiveTask = function(){
    loadContent( "/ams-ci/api/tasks/active?template=active_task", "items-active-tasks" )
}

var updateQueuedTask = function(){
    loadContent( "/ams-ci/api/tasks/pending?template=queued_task", "items-queued-tasks" )
}

var updateProjects = function(){
    loadContent( "/ams-ci/api/projects?template=project", "items-queued-tasks" )
}

var updateBuilds = function( selected ){
    loadContent( `/ams-ci/api/projects/${selected}/builds?template=builds`, "items-queued-tasks" )
}

setInterval( updateActiveTask, refreshRate * 1000 );
setInterval( updateQueuedTask, refreshRate * 1000 );
