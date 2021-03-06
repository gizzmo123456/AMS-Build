
var refreshRate = 60;           //seconds
var messageRefreshRate = 30;    //seconds    // i think we should only really do this if we are expecting a message
var selectedProject = null;
var path = "/{@www_root}/"
var api_path = path+"api"

var APPEND_MODE = {
    "NONE": 0,      // Do not append
    "ASC": 1,       // Append in order   -> top to bottom  (newest at bottom)
    "DESC": -1      // Append is reverse -> bottom to top. (newest at top)
}

var loadContent = function(url, responseElemId=null, postString=null, appendMode=APPEND_MODE.NONE, successCallback=null){

    var request = new XMLHttpRequest();

        request.onreadystatechange = function()
        {
            console.log( `URL ${url} ||| Ready State ${this.readyState} ||| Status ${this.status}` )

            if (this.readyState == 4 && this.status == 200)
            {

                if ( responseElemId != null){
                    if ( appendMode == APPEND_MODE.ASC )
                        document.getElementById(responseElemId).innerHTML += this.responseText;
                    else if ( appendMode == APPEND_MODE.DESC )
                         document.getElementById(responseElemId).innerHTML = this.responseText + document.getElementById(responseElemId).innerHTML;
                    else
                        document.getElementById(responseElemId).innerHTML = this.responseText;
                }

                if ( successCallback != null)
                    successCallback()

                console.log( `url: ${url} appended: ${appendMode} Received Response: ${this.responseText}`  );

            }
            else if ( responseElemId != null && this.status >= 300)   // should this be a thing ??
            {
                document.getElementById(responseElemId).innerHTML = ` Error: ${this.status}`
            }
        };

        if ( postString == null )
        {
            request.open("GET", url, true);
            request.send();
        }
        else
        {
            request.open("POST", url, true);
            request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
            request.send(postString);
        }

        console.log(` url ${url} sent `)

}

var updateActiveTask = function(){
    loadContent( api_path+"/tasks/active?template=active_task", "items-active-tasks" )
}

var updateQueuedTask = function(){
    loadContent( api_path+"/tasks/pending?template=queued_task", "items-queued-tasks" )
}

var updateProjects = function(){
    loadContent( api_path+"/projects?template=projects", "items-projects" )
}

var updateBuilds = function(){
    loadContent( `${api_path}/projects/name/${selectedProject}/builds?template=builds`, "items-builds" )
    // update the sites url
    document.getElementById("heading-builds").innerHTML = `Builds For ${selectedProject}`
}

var updateMessages = function(){
    postString = "clear=true"
    loadContent( api_path+"/user_messages?template=message", "message-items", postString, APPEND_MODE.DESC, showMessages )
}

var actionRequest = function( action, project, id=null, activeTask=false ){

    if ( id == null || id == "" )
        loadContent( `${path}/action/${action}/${project}` )
    else
        loadContent( `${path}/action/${action}/${project}/${id}` )

    setTimeout( updateMessages, "2000" )    // request a message update in 2 seconds

    // this is not efficient but for now at least
    if ( activeTask )
        setTimeout( updateActiveTask, "3000" )    // request a message update in 3 seconds


    setTimeout( updateQueuedTask, "3000" )    // request a message update in 3 seconds

}

var showMessages = function(){

    elem = document.getElementById("message-hold");

    if ( document.getElementById("message-items").innerHTML.trim().length == 0 )
        elem.style.display = "none";
    else
        elem.style.display="block";

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
showMessages()

setInterval( updateActiveTask, refreshRate * 1000 );
setInterval( updateQueuedTask, refreshRate * 1000 );
setInterval( updateMessages, messageRefreshRate * 1000 );
