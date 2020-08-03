
var refreshRate = 60;   //seconds
var messageRefreshRate = 30;   //seconds    // i think we should only really do this if we are expecting a message
var selectedProject = null;

var loadContent = function(url, responseElemId, postString=null, append_to_element=false, successCallback=null){

    var request = new XMLHttpRequest();

        request.onreadystatechange = function()
        {
            console.log( `URL ${url} ||| Ready State ${this.readyState} ||| Status ${this.status}` )

            if (this.readyState == 4 && this.status == 200)
            {

                if ( append_to_element )
                    document.getElementById(responseElemId).innerHTML += this.responseText;
                else
                    document.getElementById(responseElemId).innerHTML = this.responseText;

                if ( success_callback != null)
                    successCallback()

                console.log( `url: ${url} appended: ${append_to_element} Received Response: ${this.responseText}`  );

            }
            else if ( this.status >= 300)   // should this be a thing ??
            {
                document.getElementById(responseElemId).innerHTML = ` Error: ${this.status}`
            }
        };

        request.open("GET", url, true);
        if ( postString == null )
        {
            request.send();
        }
        else
        {
            request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
            request.send(postString);
        }
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

var updateMessages = function(){
    postString = "clear=true"
    loadContent( "/ams-ci/api/user_messages?template=message", "message-items", postString, true, showMessages )
}

var showMessages = function(){
    document.getElementById("message-hold").style.display="block";
}

var clearMessages = function(){
    document.getElementById("message-items").innerHTML = "";
    document.getElementById("message-hold").style.display="none";
}

var setSelectedProject = function( selected, setHash=true ){
    selectedProject = selected;
    updateBuilds();

    if ( setHash )
        window.location.hash = `#project=${selectedProject}`   // change to history.pushState ??
}

var hashChange = function(){

    hash = window.location.hash;
    hashRegex = /([a-zA-Z0-9]+)=(\w+)/;
    hashGroups = hashRegex.exec( hash );

    if ( hashGroups != null )
        if ( hashGroups[1] == "project" )
            setSelectedProject( hashGroups[2], false );
}

window.onhashchange = hashChange;

hashChange( window.location.hash );

setInterval( updateActiveTask, refreshRate * 1000 );
setInterval( updateQueuedTask, refreshRate * 1000 );
setInterval( updateMessages, messageRefreshRate * 1000 );

