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
    //TODO add hidden inputs for day and time
    $("#clonable-lesson").clone().show().insertBefore($(sender));
}

function deleteLesson(sender) {
    $(sender).parent().remove();
}
