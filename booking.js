
function thinghappened() {
    console.log("sat hello");

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
