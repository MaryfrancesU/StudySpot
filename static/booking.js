var clickable = 0;

function makebooking(spotname) {
    $.ajax({
        "url": "/actualbooking",
        "data": {
            "spotname": spotname,
            "date": $('#dateCalender').val(),
		    "stime": $('#starttime').val(),
		    "etime": $('#endtime').val(),
        },
        "type": "POST",
        "dataType": "json"
	}).done(function (response){
	    console.log(response);
    }).fail(function(xhr, status, description){
    		console.log("Error: " + status + description);
	});
}

function changepref() {

    if($('#endtime').val() < $('#starttime').val() || $('#endtime').val() == $('#starttime').val()) {
        let currOptions = $("#formspotcontainer");
	    currOptions.empty();
	    return;
    }

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

function openForm() {
    let radios = document.getElementsByName('spot');

    for(let i = 0; i < radios.length; i++) {
        if(radios[i].checked) {
            makebooking(radios[i].nextSibling.textContent);
            clickable = 1;
        }
    }

    if (clickable == 1){
        document.getElementById("popup").style.display = "block";
        document.getElementById("overlay").style.display = "block";
    }

}

function closeForm() {
  document.getElementById("popup").style.display = "none";
}