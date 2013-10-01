function validateWeeksInputKey(evt) {
    var charCode = (evt.which) ? evt.which : event.keyCode;
    if ((charCode >= 48) && (charCode <= 57)) {
        // is a digit
        return true;
    }
    if (charCode == 44) {
        // is a comma
        return true;
    }
    if (charCode == 45) {
        // is a dash
        return true;
    }
    return false;
}

function addLesson(sender) {
    var clone = $("#clonable-item").clone().show();
    clone.insertBefore($(sender));
    clone.find(".room").autocomplete({
        serviceUrl:"/autocomplete/rooms/",
        minChars:1,
    });
}

function deleteLesson(sender) {
    $(sender).parent().remove();
}
