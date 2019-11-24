function thinghappened(date) {
    $("#output").text($('dateCalender').html()); //maybe it's dateCalendar?
    console.log("sat hello");
};

function resetOptions(newOptions) {
    var currOptions = $('spot-form');

    for(let opt of newOptions) {
        var o = document.createElement("radio");
        o.className = "spot";
        o.textContent=opt.name;
        currOptions.append(o);
    }
}

function changepref() {
    $.ajax({
	  "url": "localhost:5000/selection", //change from booking to selection
        "data": {
	      "date": $('dateCalender').html(),
        // "time":
        // "pref" : {
	    //   "dummy": "sampletest",
        // },
        },
	  "type": "POST",
	  "dataType": "json"
	}).done(function (response){


	});

};

$('form').on('submit', function(event) {
$.ajax({
    'data' : {
        'date' : $('#dateCalender').val(),
    },
    'type' : 'POST',
    'url' : 'http://127.0.0.1:5000/book',
    'dataType' : 'json'
})
.done(function(data) {
    $('#output').text(data.output).show();
})
.fail(function(xhr, status, description){
    console.log("Error: " + description);
})
.always(function(xhr, status) {
    console.log("request complete w/ status: "+status);
});
event.preventDefault();
});
