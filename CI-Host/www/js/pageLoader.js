
var refreshRate = 60;   //seconds
var selectedProject = null;

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
    loadContent( "/ams-ci/api/projects?template=projects", "items-projects" )
}

var updateBuilds = function(){
    loadContent( `/ams-ci/api/projects/name/${selectedProject}/builds?template=builds`, "items-builds" )
    // update the sites url
    document.getElementById("heading-builds").innerHTML = `Builds For ${selectedProject}`
}

var setSelectedProject = function( selected, setHash=true ){
    selectedProject = selected;
    updateBuilds();

    if ( setHash )
        window.location.hash = `#project=${selectedProject}`   // change to history.pushState ??
}

window.onhashchange = function(){

    hash = window.location.hash;
    hashRegex = /([a-zA-Z0-9]+)=(\w+)/;
    hashGroups = hashRegex.exec( hash );

    if ( hashGroups != null )
        if ( hashGroups[1] == "project" )
            setSelectedProject( hashGroups[2] );
}

setInterval( updateActiveTask, refreshRate * 1000 );
setInterval( updateQueuedTask, refreshRate * 1000 );

