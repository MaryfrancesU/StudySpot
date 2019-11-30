function thinghappened() {
    console.log("the function is called");
}

function changepref() {
    $.ajax({
        "url": "/selection",
        "data": {
            "date": $('#dateCalender').val(),
		    "stime": $('#starttime').val(),
		    "etime": $('#endtime').val(),
            "food" : $('#foodfilter').prop('checked'),
            "quiet": $('#quietfilter').prop('checked'),
            "whisper": $('#whisperfilter').prop('checked'),
            "comp": $('#compfilter').prop('checked'),
        },
        "type": "POST",
        "dataType": "json"
	}).done(function (response){
	    console.log("Successfully rechose");
      console.log(response);
	    let avspots = response.availablespots;
	    let currOptions = $("#formspotcontainer");
            currOptions.empty();

        //creates a new radio input with the spot's name next to it
	    for(let opt of avspots) {
	        let label = document.createElement("label");
		    let r = document.createElement("input");
		    let text = document.createElement("label");
		    text.textContent=opt;

		    r.setAttribute("type", "radio");
		    r.name = "spot";
		    label.appendChild(r);
		    label.appendChild(text);
		    currOptions.append(label);
		    let linebreak1 = document.createElement("br");
		    currOptions.append(linebreak1);
		    let linebreak2 = document.createElement("br");
		    currOptions.append(linebreak2);

	    }
	}).fail(function(xhr, status, description){
    		console.log("Error: " + status + description);
	});
}
